from flask import render_template, jsonify, current_app
from app.models import ArticleDetail, AIEngine
from . import bp
import json
import requests
import logging

logger = logging.getLogger(__name__)

@bp.route('/')
def index():
    return render_template('dashboard/index.html')

@bp.route('/api/latest')
def latest_data():
    """Returns the latest 20 article details."""
    try:
        items = ArticleDetail.query.order_by(ArticleDetail.created_at.desc()).limit(20).all()
        data = [{
            'id': item.id,
            'title': item.title,
            'content': (item.content[:100] + '...') if item.content else '',
            'created_at': item.created_at.strftime('%Y-%m-%d %H:%M:%S') if item.created_at else ''
        } for item in items]
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching latest data: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/heatmap')
def heatmap_data():
    """
    Uses AI to analyze recent articles and return province/city stats for heatmap.
    """
    # 1. Get active AI Engine
    engine = AIEngine.query.filter_by(is_active=True).first()
    if not engine:
        # Return empty or mock if no engine
        return jsonify([])
    
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
    try:
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
        # Return empty list or error, frontend should handle gracefully
        return jsonify([])
