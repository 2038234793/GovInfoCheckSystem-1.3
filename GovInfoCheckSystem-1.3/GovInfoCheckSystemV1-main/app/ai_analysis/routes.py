from flask import render_template, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from app.models import AIEngine
from . import bp
from .core import AIAnalysisAgent
import json

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
    return render_template('ai_analysis/index.html')

@bp.route('/api/engines')
@login_required
def api_engines():
    engines = AIEngine.query.filter_by(is_active=True).all()
    return jsonify({
        "code": 0,
        "data": [{"id": e.id, "name": f"{e.provider_name} - {e.model_name}"} for e in engines]
    })

@bp.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    data = request.get_json(force=True) or {}
    engine_id = data.get('engine_id')
    prompt = data.get('prompt')
    
    if not engine_id or not prompt:
        return jsonify({"code": 1, "msg": "Engine and prompt required"})
        
    engine = AIEngine.query.get(engine_id)
    if not engine:
        return jsonify({"code": 1, "msg": "Engine not found"})
        
    def generate():
        agent = AIAnalysisAgent(engine)
        try:
            for event in agent.run(prompt):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
            
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
