import uuid
import threading
import time
import random
import json
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import CrawlItem, CrawlSource
from app.crawler import BaiduCrawler, XinhuaCrawler, ChinaSoCrawler, DynamicCrawler
from app.plugins.pachong.pachong.crawler import PachongCrawler
from app.plugins.pachong.pachong.presets import get_preset_list, get_preset, get_all_presets
from bs4 import BeautifulSoup
from . import bp

job_store = {}

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return jsonify({"error": "forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    return render_template('collect/index.html')

@bp.route('/api/sources')
@login_required
def api_sources():
    """获取所有可用站点（包括爬虫插件的预设）"""
    # 获取系统原生源
    sources = []
    
    # 获取爬虫插件预设源
    preset_list = get_preset_list()
    for preset in preset_list:
        sources.append({
            "key": preset['key'],
            "name": preset['name'],
            "category": preset['category'],
            "type": "plugin"
        })
        
    return jsonify({
        "code": 0,
        "data": sources
    })

def _run_job(job_id, keyword, limit, max_pages, sources, app):
    with app.app_context():
        job = job_store.get(job_id)
        if not job:
            return

        try:
            all_results = []
            import concurrent.futures
            
            def crawl_one_source(source_key):
                try:
                    preset = get_preset(source_key)
                    if not preset:
                        print(f"Preset not found: {source_key}")
                        return []
                    
                    crawler = PachongCrawler(preset)
                    
                    # Callback for progress update (simplified)
                    # Since we are in threads, updating job directly might be race-condition prone
                    # But for simple status text it's okay-ish or use lock
                    job["status_text"] = f"正在采集: {preset.get('name', source_key)}"
                    
                    return crawler.crawl(
                        keyword=keyword,
                        limit=limit,
                        max_pages=max_pages
                    )
                except Exception as e:
                    print(f"Error crawling {source_key}: {e}")
                    return []

            # Use ThreadPool for parallel crawling
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_source = {executor.submit(crawl_one_source, s): s for s in sources}
                for future in concurrent.futures.as_completed(future_to_source):
                    res = future.result()
                    if res:
                        all_results.extend(res)
                        # Update progress roughly
                        current = job.get("progress", 0)
                        step = 90 // len(sources)
                        job["progress"] = min(90, current + step)
            
            # Deduplicate globally
            seen = set()
            unique_results = []
            for item in all_results:
                k = item.get("url") or item.get("title")
                if k and k not in seen:
                    seen.add(k)
                    # Ensure source_name is set
                    if not item.get("source_name") and item.get("source"):
                         item["source_name"] = item["source"]
                    unique_results.append(item)
            
            job["items"] = unique_results
            job["progress"] = 100
            job["state"] = "completed"
            job["status_text"] = f"采集完成，共 {len(unique_results)} 条"
            
        except Exception as e:
            job["state"] = "error"
            job["error"] = str(e)
            job["status_text"] = f"出错: {str(e)}"

@bp.route('/api/start', methods=['POST'])
@login_required
def api_start():
    data = request.get_json(force=True) or {}
    keyword = str(data.get('q', '')).strip()
    limit = int(data.get('limit', 30))
    max_pages = int(data.get('max_pages', 3))
    
    # sources 可以是列表
    sources = data.get('src')
    if isinstance(sources, str):
        sources = [sources]
    if not sources:
        sources = ['baidu_news'] # 默认
        
    if not keyword:
        return jsonify({"error": "keyword required"}), 400
        
    job_id = uuid.uuid4().hex
    job_store[job_id] = {
        "state": "running", 
        "progress": 0, 
        "items": [], 
        "sources": sources, 
        "keyword": keyword, 
        "status_text": "正在初始化..."
    }
    
    app_obj = current_app._get_current_object()
    t = threading.Thread(target=_run_job, args=(job_id, keyword, limit, max_pages, sources, app_obj), daemon=True)
    t.start()
    
    return jsonify({"job_id": job_id})

@bp.route('/api/status')
@login_required
def api_status():
    job_id = request.args.get('job_id', '')
    job = job_store.get(job_id)
    if not job:
        return jsonify({"error": "not_found"}), 404
    return jsonify(job)

@bp.route('/api/deep', methods=['POST'])
@login_required
def api_deep():
    return jsonify({"error": "deep_disabled"}), 403

@bp.route('/api/store', methods=['POST'])
@login_required
def api_store():
    data = request.get_json(force=True) or {}
    items = data.get('items') or []
    saved = 0
    updated = 0
    keyword = data.get('keyword', '')
    
    for it in items:
        url = it.get('url') or ''
        title = it.get('title') or ''
        
        if not title:
            continue
        
        # Check existing
        existing = None
        if url:
            existing = CrawlItem.query.filter_by(url=url).first()
        if not existing and title:
            existing = CrawlItem.query.filter_by(title=title, keyword=keyword).first()
        
        if existing:
            updated += 1
        else:
            # Insert
            m = CrawlItem(
                keyword=keyword,
                title=title,
                cover=it.get('cover', ''),
                url=url,
                source=it.get('source_name') or it.get('source', ''),
                deep_crawled=False,
                deep_cover='',
                deep_summary=''
            )
            db.session.add(m)
            saved += 1
            
    try:
        db.session.commit()
        return jsonify({"saved": saved, "updated": updated})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
