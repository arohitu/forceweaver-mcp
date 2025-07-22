"""
Main web routes for the ForceWeaver MCP Server
"""
from flask import Blueprint, render_template, current_app
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page"""
    return render_template('main/index.html')

@bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('main/pricing.html')

@bp.route('/docs')
def docs():
    """Documentation page"""
    return render_template('main/docs.html')

@bp.route('/getting-started')
def getting_started():
    """Getting started guide"""
    return render_template('main/getting_started.html')

@bp.route('/status')
def status():
    """System status and health check"""
    return {
        'status': 'healthy',
        'version': '1.0.0',
        'service': 'ForceWeaver MCP Server'
    }, 200 