from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, make_response, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Report, ArticleDetail, AIEngine, CrawlItem
from datetime import datetime, timedelta
import json
import requests
import markdown
from xhtml2pdf import pisa
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
    
    # Use ReportLab native generation instead of xhtml2pdf to ensure Chinese font support
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.units import cm
    import re
    
    # Create PDF buffer
    pdf_buffer = BytesIO()
    
    # Font handling for Chinese support
    import os
    import platform
    import shutil
    
    # Prepare a persistent local font file to avoid Temp permission issues
    static_font_dir = os.path.join(current_app.static_folder, 'fonts')
    if not os.path.exists(static_font_dir):
        os.makedirs(static_font_dir)
        
    local_font_path = os.path.join(static_font_dir, 'simhei.ttf')
    font_loaded = False

    # Try to find and copy a Chinese font if not already present
    if not os.path.exists(local_font_path):
        system = platform.system()
        possible_fonts = []
        if system == "Windows":
            possible_fonts = [
                r"C:\Windows\Fonts\simhei.ttf",
                r"C:\Windows\Fonts\msyh.ttf",
                r"C:\Windows\Fonts\simsun.ttc"
            ]
        elif system == "Linux":
            possible_fonts = [
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"
            ]
            
        for f in possible_fonts:
            if os.path.exists(f):
                try:
                    shutil.copy(f, local_font_path)
                    break
                except Exception as e:
                    print(f"Failed to copy font {f}: {e}")
                    continue

    # Register the font with ReportLab if file exists
    if os.path.exists(local_font_path):
        try:
            # Register font directly in ReportLab
            pdfmetrics.registerFont(TTFont('SimHei', local_font_path))
            
            # Also register variants
            from reportlab.lib.fonts import addMapping
            addMapping('SimHei', 0, 0, 'SimHei')
            addMapping('SimHei', 0, 1, 'SimHei')
            addMapping('SimHei', 1, 0, 'SimHei')
            addMapping('SimHei', 1, 1, 'SimHei')
            
            font_loaded = True
            print(f"Successfully registered font SimHei from {local_font_path}")
        except Exception as e:
            print(f"ReportLab font registration failed: {e}")

    # Define Styles
    styles = getSampleStyleSheet()
    
    # Use SimHei if loaded, otherwise fallback to default (which will likely fail for Chinese)
    font_name = 'SimHei' if font_loaded else 'Helvetica'
    
    style_title = ParagraphStyle(
        name='ChineseTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    style_normal = ParagraphStyle(
        name='ChineseNormal',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        wordWrap='CJK', # Crucial for Chinese line breaking
        spaceAfter=10
    )
    
    style_h1 = ParagraphStyle(
        name='ChineseH1', 
        parent=styles['Heading1'], 
        fontName=font_name, 
        fontSize=18, 
        leading=22, 
        spaceAfter=10,
        spaceBefore=10
    )
    
    style_h2 = ParagraphStyle(
        name='ChineseH2', 
        parent=styles['Heading2'], 
        fontName=font_name, 
        fontSize=16, 
        leading=20, 
        spaceAfter=10,
        spaceBefore=10
    )

    # Build Story
    story = []
    
    # Add Title
    story.append(Paragraph(report.title, style_title))
    
    # Add Meta Info
    meta_info = f"生成时间：{report.created_at.strftime('%Y-%m-%d')} | 生成人：{report.user.username if report.user else 'Unknown'}"
    story.append(Paragraph(meta_info, style_normal))
    story.append(Spacer(1, 1*cm))
    
    # Process Markdown Content
    if report.content:
        # Simple Markdown parser for ReportLab
        lines = report.content.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Handle headers
            if line.startswith('# '):
                text = line[2:]
                story.append(Paragraph(text, style_h1))
            elif line.startswith('## '):
                text = line[3:]
                story.append(Paragraph(text, style_h2))
            elif line.startswith('### '):
                text = line[4:]
                story.append(Paragraph(text, style_h2)) # Map H3 to H2 style for simplicity
            
            # Handle list items
            elif line.startswith('- ') or line.startswith('* '):
                text = line[2:]
                # Bold processing: **text** -> <b>text</b>
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(f"• {text}", style_normal))
                
            # Handle normal text
            else:
                text = line
                # Bold processing: **text** -> <b>text</b>
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
                story.append(Paragraph(text, style_normal))

    # Build PDF
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, 
        topMargin=2*cm, bottomMargin=2*cm,
        title=report.title
    )
    
    try:
        doc.build(story)
    except Exception as e:
        print(f"PDF generation failed: {e}")
        return jsonify({'code': 1, 'msg': f'PDF生成失败: {str(e)}'})

    pdf_buffer.seek(0)
    
    from urllib.parse import quote
    
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    
    # Encode filename to handle Chinese characters
    encoded_filename = quote(f'{report.title}.pdf')
    response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_filename}"
    
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
