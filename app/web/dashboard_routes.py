"""
Dashboard routes for authenticated users
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app import db

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Get user stats
    api_keys_count = APIKey.query.filter_by(user_id=current_user.id, is_active=True).count()
    orgs_count = SalesforceOrg.query.filter_by(user_id=current_user.id, is_active=True).count()
    usage_count = UsageLog.query.filter_by(user_id=current_user.id).count()
    
    # Recent usage
    recent_usage = UsageLog.query.filter_by(user_id=current_user.id)\
                                 .order_by(UsageLog.created_at.desc())\
                                 .limit(5).all()
    
    return render_template('dashboard/index.html',
                         api_keys_count=api_keys_count,
                         orgs_count=orgs_count,
                         usage_count=usage_count,
                         recent_usage=recent_usage)

@bp.route('/keys')
@login_required
def keys():
    """API keys management"""
    api_keys = APIKey.query.filter_by(user_id=current_user.id)\
                          .order_by(APIKey.created_at.desc()).all()
    return render_template('dashboard/keys.html', api_keys=api_keys)

@bp.route('/keys/create', methods=['POST'])
@login_required
def create_key():
    """Create a new API key"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if not name:
        flash('API key name is required.', 'error')
        return redirect(url_for('dashboard.keys'))
    
    try:
        api_key = APIKey.create_api_key(
            user_id=current_user.id,
            name=name,
            description=description or None
        )
        
        # Show the API key once (it won't be shown again)
        flash(f'API key created successfully!', 'success')
        flash(f'Your API key: {api_key._generated_key}', 'api_key')  # Special category for styling
        flash('Please copy this key now - you won\'t see it again!', 'warning')
        
    except Exception as e:
        flash('Error creating API key. Please try again.', 'error')
        current_app.logger.error(f'Error creating API key: {e}')
    
    return redirect(url_for('dashboard.keys'))

@bp.route('/keys/<key_id>/deactivate', methods=['POST'])
@login_required
def deactivate_key(key_id):
    """Deactivate an API key"""
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first()
    
    if not api_key:
        flash('API key not found.', 'error')
        return redirect(url_for('dashboard.keys'))
    
    try:
        api_key.deactivate()
        flash(f'API key "{api_key.name}" has been deactivated.', 'success')
    except Exception as e:
        flash('Error deactivating API key.', 'error')
        current_app.logger.error(f'Error deactivating API key: {e}')
    
    return redirect(url_for('dashboard.keys'))

@bp.route('/orgs')
@login_required
def orgs():
    """Salesforce organizations management"""
    orgs = SalesforceOrg.get_user_orgs(current_user.id, active_only=False)
    return render_template('dashboard/orgs.html', orgs=orgs)

@bp.route('/orgs/create', methods=['POST'])
@login_required
def create_org():
    """Initiate Salesforce org connection via OAuth"""
    org_identifier = request.form.get('org_identifier', '').strip()
    is_sandbox = request.form.get('is_sandbox') == 'true'
    
    if not org_identifier:
        flash('Org identifier is required.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Validate org identifier format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', org_identifier):
        flash('Org identifier can only contain letters, numbers, hyphens, and underscores.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Check if org identifier already exists for this user
    existing_org = SalesforceOrg.get_by_identifier_and_user(org_identifier, current_user.id)
    if existing_org:
        flash(f'An org with identifier "{org_identifier}" already exists.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Redirect to Salesforce OAuth flow
    return redirect(url_for('auth.salesforce_authorize', 
                          org_identifier=org_identifier, 
                          is_sandbox=is_sandbox))

@bp.route('/orgs/<org_id>/deactivate', methods=['POST'])
@login_required
def deactivate_org(org_id):
    """Deactivate/disconnect a Salesforce org"""
    org = SalesforceOrg.get_by_id_and_user(org_id, current_user.id)
    
    if not org:
        flash('Salesforce org not found.', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    try:
        org.deactivate()
        flash(f'Salesforce org "{org.org_identifier}" has been disconnected.', 'success')
    except Exception as e:
        flash('Error disconnecting Salesforce org.', 'error')
        current_app.logger.error(f'Error deactivating org: {e}')
    
    return redirect(url_for('dashboard.orgs'))

@bp.route('/usage')
@login_required
def usage():
    """Usage and billing information"""
    # Get usage statistics
    total_calls = UsageLog.query.filter_by(user_id=current_user.id).count()
    successful_calls = UsageLog.query.filter_by(user_id=current_user.id, success=True).count()
    
    # Recent usage history
    recent_usage = UsageLog.query.filter_by(user_id=current_user.id)\
                                 .order_by(UsageLog.created_at.desc())\
                                 .limit(50).all()
    
    # Usage by month (for chart)
    from sqlalchemy import func, extract
    monthly_usage = db.session.query(
        extract('year', UsageLog.created_at).label('year'),
        extract('month', UsageLog.created_at).label('month'),
        func.count(UsageLog.id).label('count')
    ).filter_by(user_id=current_user.id)\
     .group_by(extract('year', UsageLog.created_at), extract('month', UsageLog.created_at))\
     .order_by(extract('year', UsageLog.created_at), extract('month', UsageLog.created_at))\
     .all()
    
    return render_template('dashboard/usage.html',
                         total_calls=total_calls,
                         successful_calls=successful_calls,
                         recent_usage=recent_usage,
                         monthly_usage=monthly_usage) 