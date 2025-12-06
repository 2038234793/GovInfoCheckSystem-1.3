import uuid
import threading
import time
import random
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import CrawlItem, CrawlSource
from app.crawler import BaiduCrawler, XinhuaCrawler, ChinaSoCrawler, DynamicCrawler
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

def _run_job(job_id, keyword, limit, max_pages, src, app):
    with app.app_context():
        # Try dynamic source first
        dynamic = CrawlSource.query.filter_by(name=src, is_active=True).first()
        if dynamic:
            import json
            config = {
                "base_url": dynamic.base_url,
                "headers": json.loads(dynamic.headers) if dynamic.headers else {},
                "params": json.loads(dynamic.params) if dynamic.params else {},
                "pagination": json.loads(dynamic.pagination) if dynamic.pagination else {},
                "selectors": json.loads(dynamic.selectors) if dynamic.selectors else {}
            }
            crawler = DynamicCrawler(config)
        else:
            if src == 'baidu':
                crawler = BaiduCrawler()
            elif src == 'xinhua':
                crawler = XinhuaCrawler()
            elif src == 'chinaso':
                crawler = ChinaSoCrawler()
            else:
                crawler = XinhuaCrawler()
    items = []
    seen = set()
    job = job_store.get(job_id)
    if not job:
        return

    try:
        if src == 'baidu':
            total_steps = max_pages * 10
            current_step = 0
            for page_index in range(max_pages):
                # Random delay to avoid rate limiting
                if page_index > 0:
                    time.sleep(random.uniform(1.5, 3.5))
                
                job["status_text"] = f"正在采集第 {page_index + 1}/{max_pages} 页..."
                pn = page_index * 10
                params = {
                    "rtt": "1",
                    "bsst": "1",
                    "cl": "2",
                    "tn": "news",
                    "rsv_dl": "ns_pc",
                    "word": keyword,
                    "pn": pn
                }
                import requests
                try:
                    # Use session for better connection pooling
                    with requests.Session() as session:
                        resp = session.get(crawler.base_url, headers=crawler.headers, params=params, timeout=15)
                        if resp.status_code != 200:
                            print(f"Status code {resp.status_code} for page {page_index}")
                            continue
                        soup = BeautifulSoup(resp.text, 'html.parser')
                        page_items = crawler._parse(soup)
                except Exception as e:
                    print(f"Error fetching page {page_index}: {e}")
                    page_items = []
                
                if not page_items:
                    # If no items found, maybe end or blocked
                    print(f"No items found on page {page_index}")
                
                for it in page_items:
                    key = it.get("url") or (it.get("title", "") + it.get("source", ""))
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(it)
                    current_step += 1
                    job["items"] = items
                    job["progress"] = min(99, int((current_step / total_steps) * 100))
                    if len(items) >= limit:
                        break
                if len(items) >= limit:
                    break
        else:
            # Xinhua or others
            job["status_text"] = "正在获取列表..."
            page_items = crawler.crawl(keyword, limit=limit, max_pages=1)
            total_steps = len(page_items) if page_items else 1
            current_step = 0
            for it in page_items:
                key = it.get("url") or it.get("title", "")
                if key in seen:
                    continue
                seen.add(key)
                if keyword:
                    try:
                        if keyword not in it.get("title", ""):
                            continue
                    except Exception:
                        pass
                items.append(it)
                current_step += 1
                job["items"] = items
                job["progress"] = min(99, int((current_step / max(1, limit)) * 100))
                if len(items) >= limit:
                    break

        job["progress"] = 100
        job["state"] = "completed"
        job["status_text"] = "采集完成"
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
    max_pages = int(data.get('max_pages', 5))
    src = (data.get('src') or 'baidu').lower()
    if src == 'baidu' and not keyword:
        return jsonify({"error": "keyword required"}), 400
    job_id = uuid.uuid4().hex
    job_store[job_id] = {"state": "running", "progress": 0, "items": [], "src": src, "keyword": keyword, "status_text": "正在初始化..."}
    app_obj = current_app._get_current_object()
    t = threading.Thread(target=_run_job, args=(job_id, keyword, limit, max_pages, src, app_obj), daemon=True)
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
    for it in items:
        url = it.get('url') or ''
        if not url:
            continue
        
        # Check existing
        existing = CrawlItem.query.filter_by(url=url).first()
        
        if existing:
            # Update
            existing.keyword = it.get('keyword') or data.get('keyword') or existing.keyword
            existing.title = it.get('title') or existing.title
            existing.cover = it.get('cover') or existing.cover
            existing.source = it.get('source') or existing.source
            existing.deep_crawled = bool(it.get('deep')) or existing.deep_crawled
            existing.deep_cover = it.get('deep_cover') or it.get('cover') or existing.deep_cover
            existing.deep_summary = it.get('deep_summary') or existing.deep_summary
            updated += 1
        else:
            # Insert
            m = CrawlItem(
                keyword=it.get('keyword') or data.get('keyword') or '',
                title=it.get('title') or '',
                cover=it.get('cover') or '',
                url=url,
                source=it.get('source') or '',
                deep_crawled=bool(it.get('deep')),
                deep_cover=it.get('deep_cover') or it.get('cover') or '',
                deep_summary=it.get('deep_summary') or ''
            )
            db.session.add(m)
            saved += 1
    db.session.commit()
    return jsonify({"saved": saved, "updated": updated})
