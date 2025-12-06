from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Report, ArticleDetail, AIEngine, CrawlItem
from datetime import datetime, timedelta
import json
import requests
import markdown
from xhtml2pdf import pisa
from io import BytesIO

report_mgmt_bp = Blueprint('report_mgmt', __name__, template_folder='templates', url_prefix='/report_mgmt')

@report_mgmt_bp.route('/')
@login_required
def index():
    return render_template('report_mgmt/index.html')

@report_mgmt_bp.route('/api/list')
@login_required
def api_list():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    industry = request.args.get('industry')
    
    query = Report.query
    if industry:
        query = query.filter(Report.industry.like(f'%{industry}%'))
        
    pagination = query.order_by(Report.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    
    return jsonify({
        'code': 0,
        'msg': '',
        'count': pagination.total,
        'data': [item.to_dict() for item in pagination.items]
    })

@report_mgmt_bp.route('/generate')
@login_required
def generate():
    engines = AIEngine.query.filter_by(is_active=True).all()
    return render_template('report_mgmt/generate.html', engines=engines)

@report_mgmt_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    data = request.get_json()
    industry = data.get('industry')
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    engine_id = data.get('engine_id')
    
    if not all([industry, start_date_str, end_date_str, engine_id]):
        return jsonify({'code': 1, 'msg': '请填写完整信息'})
    
    # Strip input
    industry = industry.strip()
        
    # Fetch data
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    except ValueError:
        return jsonify({'code': 1, 'msg': '日期格式错误'})
        
    # Query articles based on time range and joined with CrawlItem for source info
    # Filter by industry/keyword in Title, Content, Keyword, or Source
    
    # Using outerjoin to include items without details
    items = db.session.query(CrawlItem, ArticleDetail).outerjoin(
        ArticleDetail, CrawlItem.id == ArticleDetail.crawl_item_id
    ).filter(
        CrawlItem.created_at.between(start_date, end_date)
    ).filter(
        (CrawlItem.title.contains(industry)) | 
        (CrawlItem.keyword.contains(industry)) |
        (CrawlItem.source.contains(industry)) |
        (ArticleDetail.content.contains(industry))
    ).limit(50).all() # Limit to 50 articles to avoid token limit overflow
    
    if not items:
        return jsonify({'code': 1, 'msg': f'该时间段内未找到关于“{industry}”的数据'})
        
    # Prepare prompt with richer context
    articles_text_list = []
    for item_tuple in items:
        crawl_item = item_tuple[0]
        detail = item_tuple[1]
        
        source_name = crawl_item.source if crawl_item.source else '未知来源'
        pub_time = crawl_item.created_at.strftime('%Y-%m-%d')
        
        content_summary = "（无详细内容）"
        if detail and detail.content:
            content_summary = detail.content[:200]
        elif crawl_item.deep_summary:
            content_summary = crawl_item.deep_summary[:200]
            
        articles_text_list.append(f"【{source_name} {pub_time}】标题：{crawl_item.title}\n内容摘要：{content_summary}...")
        
    articles_text = "\n\n".join(articles_text_list)
    
    prompt = f"""
    请根据以下从数据库中检索到的【{industry}】行业的新闻资讯，生成一份专业的行业分析报告。
    报告应包含：行业动态总结、热点事件分析、未来趋势预测。
    
    资讯列表：
    {articles_text}
    """
    
    # Call AI Engine
    engine = AIEngine.query.get(engine_id)
    if not engine:
        return jsonify({'code': 1, 'msg': 'AI引擎不存在'})
        
    try:
        ai_response = call_ai_api(engine, prompt)
    except Exception as e:
        return jsonify({'code': 1, 'msg': f'AI生成失败: {str(e)}'})
        
    # Save Report
    report = Report(
        title=f'{industry}行业分析报告 ({start_date_str} ~ {end_date_str})',
        content=ai_response,
        industry=industry,
        time_range=f'{start_date_str} ~ {end_date_str}',
        report_type='custom',
        user_id=current_user.id
    )
    db.session.add(report)
    db.session.commit()
    
    return jsonify({'code': 0, 'msg': '报告生成成功'})

def call_ai_api(engine, prompt):
    # Simple implementation for OpenAI-compatible APIs
    headers = {
        "Authorization": f"Bearer {engine.api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": engine.model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(f"{engine.api_url}/chat/completions", headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        # Fallback or specific provider handling could be added here
        raise e

@report_mgmt_bp.route('/view/<int:id>')
@login_required
def view(id):
    report = Report.query.get_or_404(id)
    # Convert Markdown to HTML for display
    html_content = markdown.markdown(report.content)
    return render_template('report_mgmt/view.html', report=report, html_content=html_content)

@report_mgmt_bp.route('/download/<int:id>')
@login_required
def download(id):
    report = Report.query.get_or_404(id)
    html_content = markdown.markdown(report.content)
    
    # Create PDF
    pdf_buffer = BytesIO()
    
    # Simple HTML template for PDF
    pdf_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: "Microsoft YaHei", sans-serif; }}
            h1 {{ text-align: center; color: #333; }}
            .meta {{ text-align: center; color: #666; margin-bottom: 30px; }}
            .content {{ line-height: 1.6; }}
        </style>
    </head>
    <body>
        <h1>{report.title}</h1>
        <div class="meta">
            <p>生成时间：{report.created_at.strftime('%Y-%m-%d')}</p>
            <p>生成人：{report.user.username if report.user else 'Unknown'}</p>
        </div>
        <div class="content">
            {html_content}
        </div>
    </body>
    </html>
    """
    
    # Need to handle fonts for Chinese characters in xhtml2pdf if needed, 
    # usually requires registering fonts. For simplicity, we rely on system fonts or basic support.
    # If Chinese doesn't show, we might need to add font registration code.
    
    pisa_status = pisa.CreatePDF(pdf_html, dest=pdf_buffer, encoding='utf-8')
    
    if pisa_status.err:
        return "PDF generation error", 500
        
    pdf_buffer.seek(0)
    
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={report.title}.pdf'
    
    return response

@report_mgmt_bp.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    id = request.json.get('id')
    report = Report.query.get(id)
    if report:
        db.session.delete(report)
        db.session.commit()
        return jsonify({'code': 0, 'msg': '删除成功'})
    return jsonify({'code': 1, 'msg': '报告不存在'})
