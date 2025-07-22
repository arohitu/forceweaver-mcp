"""
Authentication API endpoints (v1.0)
"""
from flask import Blueprint

bp = Blueprint('auth_api', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """User login API"""
    return {'message': 'Login API - Coming Soon'}, 200

@bp.route('/register', methods=['POST'])
def register():
    """User registration API"""
    return {'message': 'Registration API - Coming Soon'}, 200 