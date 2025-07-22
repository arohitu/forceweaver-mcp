"""
Dashboard routes for user management interface
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app import db

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Main dashboard"""
    # Get user statistics
    api_keys = APIKey.get_user_keys(current_user.id)
    orgs = SalesforceOrg.get_user_orgs(current_user.id)
    
    # Get recent usage
    recent_usage = UsageLog.get_user_usage(current_user.id, limit=10)
    
    # Get this month's usage stats
    monthly_stats = UsageLog.get_monthly_usage(current_user.id)
    
    return render_template('dashboard/index.html', 
                         api_keys=api_keys,
                         orgs=orgs,
                         recent_usage=recent_usage,
                         monthly_stats=monthly_stats)

@bp.route('/keys')
@login_required
def keys():
    """API keys management"""
    api_keys = APIKey.get_user_keys(current_user.id, include_inactive=True)
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
        flash(f'API key created successfully! Your key is: {api_key._generated_key}', 'success')
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
    orgs = SalesforceOrg.get_user_orgs(current_user.id, include_inactive=True)
    return render_template('dashboard/orgs.html', orgs=orgs)

@bp.route('/orgs/create', methods=['POST'])
@login_required
def create_org():
    """Create a new Salesforce org configuration"""
    org_identifier = request.form.get('org_identifier', '').strip().lower()
    instance_url = request.form.get('instance_url', '').strip()
    client_id = request.form.get('client_id', '').strip()
    client_secret = request.form.get('client_secret', '').strip()
    is_sandbox = bool(request.form.get('is_sandbox'))
    
    # Validation
    errors = []
    
    if not org_identifier:
        errors.append('Organization identifier is required.')
    elif not org_identifier.replace('_', '').replace('-', '').isalnum():
        errors.append('Organization identifier can only contain letters, numbers, hyphens, and underscores.')
    
    if not instance_url:
        errors.append('Salesforce instance URL is required.')
    elif not instance_url.startswith('https://'):
        errors.append('Instance URL must start with https://')
    
    if not client_id:
        errors.append('Client ID is required.')
    
    if not client_secret:
        errors.append('Client Secret is required.')
    
    # Check if org identifier already exists for this user
    if SalesforceOrg.get_user_org(current_user.id, org_identifier):
        errors.append('An organization with this identifier already exists.')
    
    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('dashboard.orgs'))
    
    try:
        org = SalesforceOrg.create_org(
            user_id=current_user.id,
            org_identifier=org_identifier,
            instance_url=instance_url,
            client_id=client_id,
            client_secret=client_secret,
            is_sandbox=is_sandbox
        )
        
        flash(f'Salesforce org "{org_identifier}" created successfully!', 'success')
        
    except Exception as e:
        flash('Error creating Salesforce org configuration.', 'error')
        current_app.logger.error(f'Error creating Salesforce org: {e}')
    
    return redirect(url_for('dashboard.orgs'))

@bp.route('/usage')
@login_required
def usage():
    """Usage statistics and billing"""
    # Get current month usage
    current_month_stats = UsageLog.get_monthly_usage(current_user.id)
    
    # Get recent usage logs
    recent_usage = UsageLog.get_user_usage(current_user.id, limit=50)
    
    return render_template('dashboard/usage.html',
                         current_month=current_month_stats,
                         recent_usage=recent_usage) 