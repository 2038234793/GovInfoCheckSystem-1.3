"""
Pachong 插件路由
提供 RESTful API 接口
"""

import uuid
import threading
import json
import logging
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from . import pachong_bp
from .plugin import PachongPlugin
from .presets import get_preset_list, get_preset, get_all_presets, get_categories

logger = logging.getLogger(__name__)

# 任务存储
job_store = {}

# 插件实例
plugin = PachongPlugin()


def admin_required(f):
    """管理员权限装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return jsonify({"code": 1, "error": "forbidden"}), 403
        return f(*args, **kwargs)
    return decorated_function


@pachong_bp.route('/')
@login_required
def index():
    """插件首页"""
    return render_template('pachong/index.html')


@pachong_bp.route('/api/info')
@login_required
def api_info():
    """获取插件信息"""
    return jsonify({
        "code": 0,
        "data": {
            "name": plugin.name,
            "version": plugin.version,
            "description": plugin.description,
            "source_count": len(get_all_presets())
        }
    })


@pachong_bp.route('/api/sources')
@login_required
def api_sources():
    """获取所有可用站点"""
    sources = get_preset_list()
    categories = get_categories()
    return jsonify({
        "code": 0,
        "data": {
            "sources": sources,
            "categories": categories,
            "total": len(sources)
        }
    })


@pachong_bp.route('/api/source/<key>')
@login_required
def api_source_detail(key):
    """获取站点详情"""
    config = get_preset(key)
    if not config:
        return jsonify({"code": 1, "msg": "站点不存在"})
    return jsonify({"code": 0, "data": config})


@pachong_bp.route('/api/crawl', methods=['POST'])
@login_required
@admin_required
def api_crawl():
    """
    执行爬取（同步）
    
    请求体：
        {
            "keyword": "关键词",
            "sources": ["baidu_news", "xinhua"],
            "limit": 30,
            "max_pages": 3
        }
    """
    data = request.get_json(force=True) or {}
    keyword = str(data.get('keyword', '')).strip()
    sources = data.get('sources', ['baidu_news'])
    limit = int(data.get('limit', 30))
    max_pages = int(data.get('max_pages', 3))
    
    if not keyword:
        return jsonify({"code": 1, "msg": "请输入关键词"})
    
    if not sources:
        return jsonify({"code": 1, "msg": "请选择至少一个站点"})
    
    try:
        results = plugin.crawl(
            keyword=keyword,
            sources=sources,
            limit=limit,
            max_pages=max_pages,
            parallel=True
        )
        return jsonify({
            "code": 0,
            "data": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        return jsonify({"code": 1, "msg": str(e)})


@pachong_bp.route('/api/crawl/async', methods=['POST'])
@login_required
@admin_required
def api_crawl_async():
    """
    执行爬取（异步）
    
    返回 job_id，通过 /api/crawl/status 查询进度
    """
    data = request.get_json(force=True) or {}
    keyword = str(data.get('keyword', '')).strip()
    sources = data.get('sources', ['baidu_news'])
    limit = int(data.get('limit', 30))
    max_pages = int(data.get('max_pages', 3))
    
    if not keyword:
        return jsonify({"code": 1, "msg": "请输入关键词"})
    
    if not sources:
        return jsonify({"code": 1, "msg": "请选择至少一个站点"})
    
    job_id = uuid.uuid4().hex
    job_store[job_id] = {
        "state": "running",
        "progress": 0,
        "items": [],
        "sources": sources,
        "keyword": keyword,
        "completed_sources": [],
        "status_text": f"正在从 {len(sources)} 个站点采集..."
    }
    
    def run_job():
        job = job_store.get(job_id)
        if not job:
            return
        
        def on_progress(source_name, count):
            job["completed_sources"].append(source_name)
            job["status_text"] = f"已完成: {source_name} ({count}条)"
            job["progress"] = int(len(job["completed_sources"]) / len(sources) * 100)
        
        try:
            results = plugin.crawl(
                keyword=keyword,
                sources=sources,
                limit=limit,
                max_pages=max_pages,
                parallel=True,
                on_progress=on_progress
            )
            job["items"] = results
            job["progress"] = 100
            job["state"] = "completed"
            job["status_text"] = f"采集完成，共 {len(results)} 条"
        except Exception as e:
            job["state"] = "error"
            job["error"] = str(e)
            job["status_text"] = f"出错: {str(e)}"
    
    t = threading.Thread(target=run_job, daemon=True)
    t.start()
    
    return jsonify({"code": 0, "job_id": job_id})


@pachong_bp.route('/api/crawl/status')
@login_required
@admin_required
def api_crawl_status():
    """查询异步任务状态"""
    job_id = request.args.get('job_id', '')
    job = job_store.get(job_id)
    if not job:
        return jsonify({"code": 1, "msg": "任务不存在"}), 404
    return jsonify({"code": 0, "data": job})


@pachong_bp.route('/api/test', methods=['POST'])
@login_required
@admin_required
def api_test():
    """
    测试爬虫配置
    
    请求体：
        {
            "config": {...},
            "keyword": "测试关键词"
        }
    """
    data = request.get_json(force=True) or {}
    config = data.get('config', {})
    keyword = data.get('keyword', '测试')
    
    if not config:
        return jsonify({"code": 1, "msg": "请提供配置"})
    
    result = plugin.test_config(config, keyword)
    return jsonify({"code": 0, "data": result})


@pachong_bp.route('/api/presets')
@login_required
def api_presets():
    """获取所有预设（用于下拉选择）"""
    return jsonify({"code": 0, "data": get_preset_list()})


@pachong_bp.route('/api/preset/<key>')
@login_required
def api_preset_detail(key):
    """获取预设详情"""
    preset = get_preset(key)
    if not preset:
        return jsonify({"code": 1, "msg": "预设不存在"})
    return jsonify({"code": 0, "data": preset})


@pachong_bp.route('/api/store', methods=['POST'])
@login_required
@admin_required
def api_store():
    """
    将爬取结果存储到数据仓库
    
    请求体：
        {
            "items": [...],      // 爬取结果列表
            "keyword": "关键词"   // 搜索关键词
        }
    """
    from app import db
    from app.models import CrawlItem
    
    data = request.get_json(force=True) or {}
    items = data.get('items', [])
    keyword = data.get('keyword', '')
    
    if not items:
        return jsonify({"code": 1, "msg": "没有数据需要存储"})
    
    saved_count = 0
    skipped_count = 0
    
    for item in items:
        title = item.get('title', '').strip()
        url = item.get('url', '').strip()
        
        if not title:
            skipped_count += 1
            continue
        
        # 检查是否已存在（通过URL或标题去重）
        existing = None
        if url:
            existing = CrawlItem.query.filter_by(url=url).first()
        if not existing and title:
            existing = CrawlItem.query.filter_by(title=title, keyword=keyword).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 创建新记录
        crawl_item = CrawlItem(
            keyword=keyword,
            title=title,
            cover=item.get('cover', ''),
            url=url,
            source=item.get('source_name') or item.get('source', '')
        )
        db.session.add(crawl_item)
        saved_count += 1
    
    try:
        db.session.commit()
        logger.info(f"Stored {saved_count} items to warehouse, skipped {skipped_count}")
        return jsonify({
            "code": 0,
            "msg": f"成功存储 {saved_count} 条数据，跳过 {skipped_count} 条重复数据",
            "saved": saved_count,
            "skipped": skipped_count
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Store error: {e}")
        return jsonify({"code": 1, "msg": f"存储失败: {str(e)}"})


@pachong_bp.route('/api/store_job', methods=['POST'])
@login_required
@admin_required
def api_store_job():
    """
    将指定任务的结果存储到数据仓库
    
    请求体：
        {
            "job_id": "任务ID"
        }
    """
    from app import db
    from app.models import CrawlItem
    
    data = request.get_json(force=True) or {}
    job_id = data.get('job_id', '')
    
    job = job_store.get(job_id)
    if not job:
        return jsonify({"code": 1, "msg": "任务不存在"})
    
    if job.get('state') != 'completed':
        return jsonify({"code": 1, "msg": "任务尚未完成"})
    
    items = job.get('items', [])
    keyword = job.get('keyword', '')
    
    if not items:
        return jsonify({"code": 1, "msg": "没有数据需要存储"})
    
    saved_count = 0
    skipped_count = 0
    
    for item in items:
        title = item.get('title', '').strip()
        url = item.get('url', '').strip()
        
        if not title:
            skipped_count += 1
            continue
        
        # 检查是否已存在
        existing = None
        if url:
            existing = CrawlItem.query.filter_by(url=url).first()
        if not existing and title:
            existing = CrawlItem.query.filter_by(title=title, keyword=keyword).first()
        
        if existing:
            skipped_count += 1
            continue
        
        crawl_item = CrawlItem(
            keyword=keyword,
            title=title,
            cover=item.get('cover', ''),
            url=url,
            source=item.get('source_name') or item.get('source', '')
        )
        db.session.add(crawl_item)
        saved_count += 1
    
    try:
        db.session.commit()
        return jsonify({
            "code": 0,
            "msg": f"成功存储 {saved_count} 条数据，跳过 {skipped_count} 条重复数据",
            "saved": saved_count,
            "skipped": skipped_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 1, "msg": f"存储失败: {str(e)}"})
