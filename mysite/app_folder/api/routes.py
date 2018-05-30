from flask import request, abort, jsonify
from app_folder.api import bp

@bp.route('spark', methods=['GET', 'POST'])
def route_webhook():
    hook_data = request.json
    data = hook_data.get('data')
