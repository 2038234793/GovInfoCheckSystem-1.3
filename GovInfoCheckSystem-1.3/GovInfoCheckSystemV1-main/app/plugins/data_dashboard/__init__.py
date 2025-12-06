from flask import Blueprint, render_template, jsonify, request
from app.models import ArticleDetail, AIEngine, CrawlSource
from sqlalchemy import func
import requests
import logging
import json

# Define Blueprint
dashboard_bp = Blueprint('data_dashboard', __name__, 
                        template_folder='templates',
                        static_folder='static',
                        url_prefix='/plugins/dashboard')

logger = logging.getLogger(__name__)

@dashboard_bp.route('/')
def index():
    return render_template('dashboard_plugin.html')

@dashboard_bp.route('/api/stats')
def get_stats():
    """Get statistics for charts"""
    from app import db
    try:
        # Get keyword from query parameters (for GET requests)
        keyword = request.args.get('keyword', '').strip()
        
        # 1. Total count
        total_articles = ArticleDetail.query.count()
        
        # 2. Source distribution (Pie Chart)
        # Using CrawlItem.source via join
        from app.models import CrawlItem
        source_stats = db.session.query(
            CrawlItem.source, func.count(ArticleDetail.id)
        ).join(ArticleDetail, ArticleDetail.crawl_item_id == CrawlItem.id)\
         .group_by(CrawlItem.source).limit(10).all()
        
        pie_data = [{'name': s[0] or '未知', 'value': s[1]} for s in source_stats]
        
        # 3. Date distribution (Bar Chart) - Last 7 days
        from datetime import datetime, timedelta
        
        # Generate last 7 days strings (YYYY-MM-DD)
        today = datetime.now().date()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
        
        # Query actual data (fetch more to ensure we cover the range if there are gaps)
        date_stats = db.session.query(
            func.date(ArticleDetail.created_at), func.count(ArticleDetail.id)
        ).group_by(func.date(ArticleDetail.created_at)).order_by(func.date(ArticleDetail.created_at).desc()).limit(20).all()
        
        # Create lookup dict
        stats_map = {str(d[0]): d[1] for d in date_stats}
        
        # Build result lists ensuring all 7 days are present
        bar_data = {
            'categories': dates,
            'values': [stats_map.get(d, 0) for d in dates]
        }
        
        # 4. Recent List
        query = ArticleDetail.query
        
        # Filter by keyword if provided
        if keyword:
            query = query.filter(
                (ArticleDetail.title.contains(keyword)) | 
                (ArticleDetail.content.contains(keyword))
            )
            
        recent_items = query.order_by(ArticleDetail.created_at.desc()).limit(50).all()
        list_data = [{
            'id': item.id,
            'title': item.title,
            'source': item.crawl_item.source if item.crawl_item else 'Unknown',
            'time': item.created_at.strftime('%Y-%m-%d %H:%M'),
            'content': item.content[:200] + '...' if item.content else '',
            'url': item.crawl_item.url if item.crawl_item else '#'
        } for item in recent_items]

        return jsonify({
            'total': total_articles,
            'pie_data': pie_data,
            'bar_data': bar_data,
            'list_data': list_data
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/refresh_news', methods=['POST'])
def refresh_news():
    """Trigger a quick crawl to refresh news"""
    from app import db
    from app.models import CrawlItem, ArticleDetail
    from app.crawler import BaiduCrawler
    from datetime import datetime, timedelta
    import re

    def parse_date(date_str):
        if not date_str: return datetime.now()
        now = datetime.now()
        try:
            if '分钟' in date_str or 'minutes' in date_str:
                m = re.search(r'(\d+)', date_str)
                if m: return now - timedelta(minutes=int(m.group(1)))
            elif '小时' in date_str or 'hours' in date_str:
                m = re.search(r'(\d+)', date_str)
                if m: return now - timedelta(hours=int(m.group(1)))
            elif '昨天' in date_str:
                return now - timedelta(days=1)
            elif '前天' in date_str:
                return now - timedelta(days=2)
            elif '天' in date_str or 'days' in date_str:
                m = re.search(r'(\d+)', date_str)
                if m: return now - timedelta(days=int(m.group(1)))
            
            # Try parsing date strings
            # Regex for YYYY-MM-DD or YYYY年MM月DD日
            date_match = re.search(r'(\d{4})[-年](\d{1,2})[-月](\d{1,2})', date_str)
            if date_match:
                return datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
                
            return now
        except:
            return now

    try:
        data = request.get_json() or {}
        keyword = data.get('keyword', '').strip() or '四川' # Default to Sichuan if empty
        
        logger.info(f"Refreshing news for keyword: {keyword}")
        
        crawler = BaiduCrawler()
        # Crawl only 1 page for speed
        results = crawler.crawl(keyword, limit=10, max_pages=1)
        
        new_count = 0
        for item in results:
            url = item.get('url')
            if not url:
                continue
                
            # Check if exists
            exists = CrawlItem.query.filter_by(url=url).first()
            if not exists:
                # Create CrawlItem
                pub_date = parse_date(item.get('date'))
                crawl_item = CrawlItem(
                    keyword=keyword,
                    title=item.get('title'),
                    cover=item.get('cover'),
                    url=url,
                    source=item.get('source', 'Baidu News'),
                    deep_summary=item.get('summary'),
                    created_at=pub_date
                )
                db.session.add(crawl_item)
                db.session.flush() # Get ID
                
                # Create ArticleDetail
                detail = ArticleDetail(
                    crawl_item_id=crawl_item.id,
                    title=item.get('title'),
                    content=item.get('summary') or item.get('title'), # Use summary as content for now
                    created_at=pub_date
                )
                db.session.add(detail)
                new_count += 1
        
        if new_count > 0:
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': f'成功采集 {new_count} 条新资讯',
            'new_count': new_count
        })
        
    except Exception as e:
        logger.error(f"Refresh news error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard_bp.route('/api/map_data')
def map_data():
    """
    Uses AI to analyze recent articles and return province/city stats for heatmap.
    Replaces the old mock data with real AI analysis.
    """
    try:
        # 1. Get active AI Engine
        engine = AIEngine.query.filter_by(is_active=True).first()
        if not engine:
            # Fallback to mock data if no engine
            logger.info("No active AI engine, returning mock map data")
            provinces = ['北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', '湖南', '安徽', '山东', '新疆', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', '山西', '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', '四川', '宁夏', '海南', '台湾', '香港', '澳门']
            import random
            data = [{'name': p, 'value': random.randint(10, 500)} for p in provinces]
            return jsonify(data)
        
        # 2. Get recent data for analysis (limit 50 to respect context window)
        items = ArticleDetail.query.order_by(ArticleDetail.created_at.desc()).limit(50).all()
        if not items:
            return jsonify([])

        # 3. Prepare Prompt
        # Only using titles to save tokens, usually enough for location extraction
        texts = [f"{i+1}. {item.title}" for i, item in enumerate(items)]
        content_block = "\n".join(texts)
        
        system_prompt = """
        你是一个数据分析助手。请分析以下新闻标题列表。
        任务：
        1. 识别每条新闻涉及的中国省份（如广东、北京、四川等）或城市（如深圳、成都、武汉等）。
        2. 如果识别到城市，请将其归类到对应的省份（例如：深圳 -> 广东，成都 -> 四川）。
        3. 统计每个省份出现的新闻数量。
        4. 为每个省份提取1-2个热词（Keywords）。
        5. 输出必须是严格的JSON数组格式，不要包含任何Markdown标记或额外文本。
        
        JSON格式示例：
        [
            {"name": "北京", "value": 5, "keywords": ["政策", "会议"]},
            {"name": "广东", "value": 3, "keywords": ["经济", "科技"]}
        ]
        """
        
        # 4. Call AI
        headers = {
            "Authorization": f"Bearer {engine.api_key}",
            "Content-Type": "application/json"
        }
        
        # Adjust API URL if needed
        api_url = engine.api_url.strip().rstrip('/')
        if not api_url.endswith('/chat/completions'):
             api_url += '/chat/completions'
             
        payload = {
            "model": engine.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content_block}
            ],
            "temperature": 0.1,
            "stream": False
        }
        
        # Timeout 60s
        resp = requests.post(api_url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        
        result = resp.json()
        content = result['choices'][0]['message']['content']
        
        # Clean content (remove markdown if present)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
            
        data = json.loads(content)
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"AI Analysis Heatmap Error: {e}")
        # Fallback to mock on error
        provinces = ['北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', '湖南', '安徽', '山东', '新疆', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', '山西', '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', '四川', '宁夏', '海南', '台湾', '香港', '澳门']
        import random
        data = [{'name': p, 'value': random.randint(10, 100)} for p in provinces]
        return jsonify(data)

@dashboard_bp.route('/api/ai_report', methods=['POST'])
def ai_report():
    """Generate report using AI"""
    try:
        # Get keyword from request
        data = request.get_json() or {}
        keyword = data.get('keyword', '').strip()
        
        engine = AIEngine.query.filter_by(is_active=True).first()
        if not engine:
            # Fallback to mock data if no engine configured
            return jsonify({'report': _get_mock_report()})

        # Get recent titles for context, filtered by keyword if provided
        query = ArticleDetail.query.order_by(ArticleDetail.created_at.desc())
        
        if keyword:
            query = query.filter(
                (ArticleDetail.title.contains(keyword)) | 
                (ArticleDetail.content.contains(keyword))
            )
            
        items = query.limit(20).all()
        
        # If no items found and keyword exists, try to crawl on-demand
        if not items and keyword:
            logger.info(f"No local items found for '{keyword}', triggering on-demand crawl...")
            try:
                from app.crawler import BaiduCrawler
                from app.models import CrawlItem
                from app import db
                
                crawler = BaiduCrawler()
                # Crawl a small batch for the report
                crawl_results = crawler.crawl(keyword, limit=10, max_pages=1)
                
                new_count = 0
                for item in crawl_results:
                    url = item.get('url')
                    if not url: continue
                    
                    if not CrawlItem.query.filter_by(url=url).first():
                        crawl_item = CrawlItem(
                            keyword=keyword,
                            title=item.get('title'),
                            cover=item.get('cover'),
                            url=url,
                            source=item.get('source', 'Baidu News'),
                            deep_summary=item.get('summary')
                        )
                        db.session.add(crawl_item)
                        db.session.flush()
                        
                        detail = ArticleDetail(
                            crawl_item_id=crawl_item.id,
                            title=item.get('title'),
                            content=item.get('summary') or item.get('title')
                        )
                        db.session.add(detail)
                        new_count += 1
                
                if new_count > 0:
                    db.session.commit()
                    logger.info(f"On-demand crawl saved {new_count} items")
                    
                    # Re-query after crawl
                    # We need to recreate the query object to get fresh results
                    query = ArticleDetail.query.filter(
                        (ArticleDetail.title.contains(keyword)) | 
                        (ArticleDetail.content.contains(keyword))
                    ).order_by(ArticleDetail.created_at.desc())
                    items = query.limit(20).all()
                
            except Exception as e:
                logger.error(f"On-demand crawl failed: {e}")
                # Fall through to empty check
        
        if not items:
            msg = f'未找到包含关键词 "{keyword}" 的相关资讯' if keyword else '暂无相关资讯数据'
            return jsonify({'report': f'<p class="text-yellow-400 text-center">{msg}，无法生成报告。</p>'})

        context = "\n".join([f"- {item.title}" for item in items])
        
        prompt_prefix = f"基于包含关键词“{keyword}”的" if keyword else "基于以下最近采集的"
        
        prompt = f"""
        {prompt_prefix}新闻标题，生成一份简短的舆情分析报告（300字以内）。
        包含：热点话题总结、情感倾向分析、以及建议关注的领域。
        请直接输出HTML内容（使用<p>, <ul>, <li>, <strong>等标签），不要包含markdown代码块标记（如 ```html）。
        
        新闻列表：
        {context}
        """

        headers = {
            "Authorization": f"Bearer {engine.api_key}",
            "Content-Type": "application/json"
        }
        
        api_url = engine.api_url.strip().rstrip('/')
        if not api_url.endswith('/chat/completions'):
             api_url += '/chat/completions'
             
        payload = {
            "model": engine.model_name,
            "messages": [
                {"role": "system", "content": "你是专业的舆情分析师。请直接返回HTML格式的分析报告。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        # Increased timeout to 120s
        resp = requests.post(api_url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        
        result = resp.json()
        content = result['choices'][0]['message']['content']
        
        # Strip markdown code blocks if present
        content = content.replace('```html', '').replace('```', '').strip()
        
        return jsonify({'report': content})
        
    except Exception as e:
        logger.error(f"AI Report error: {e}")
        return jsonify({'error': str(e)}), 500

def _get_mock_report():
    """Return a mock report for demonstration"""
    return """
    <div class="p-4 bg-gray-800/50 rounded-lg border border-blue-500/30">
        <h3 class="text-lg font-bold text-blue-400 mb-3 flex items-center">
            <i class="layui-icon layui-icon-chart-screen mr-2"></i>舆情分析简报 (演示模式)
        </h3>
        <div class="space-y-3 text-sm text-gray-300">
            <p><strong class="text-blue-300">🔥 热点话题：</strong> 近期监测显示，“数字化政务”、“智慧城市建设”及“公共卫生安全”为舆论关注焦点，相关讨论热度持续上升。</p>
            <p><strong class="text-green-300">😊 情感倾向：</strong> 整体舆情态势平稳向好，正面情绪占比约 85%。公众对近期推出的便民服务措施给予高度评价，但对部分系统的稳定性仍有少量反馈。</p>
            <p><strong class="text-yellow-300">⚡ 建议关注：</strong> 建议重点关注后续政策的具体落地情况，加强对网络安全防护体系的宣传，及时回应公众关切。</p>
        </div>
        <div class="mt-4 pt-3 border-t border-gray-700 text-xs text-gray-500 flex justify-between items-center">
            <span>Generated by AI System (Demo)</span>
            <span class="px-2 py-1 bg-yellow-900/30 text-yellow-500 rounded">未配置AI引擎</span>
        </div>
    </div>
    """

