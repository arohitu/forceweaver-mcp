"""
Dashboard routes using simple session-based authentication
"""
import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import db, get_current_user, login_required
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app.models.rate_configuration import RateConfiguration

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required 
def index():
    """Dashboard home with authentication check"""
    current_app.logger.info(f"Dashboard access - session: {dict(session)}")
    
    user = get_current_user()
    if not user:
        current_app.logger.warning("No authenticated user found")
        return redirect(url_for('auth.login'))
    
    current_app.logger.info(f"Dashboard accessed by user: {user.email}")
    
    # Get user data
    try:
        # Get API keys
        api_keys = APIKey.query.filter_by(user_id=user.id).order_by(APIKey.created_at.desc()).all()
        active_api_keys = [key for key in api_keys if key.is_active]
        
        # Get Salesforce orgs  
        orgs = SalesforceOrg.query.filter_by(user_id=user.id, is_active=True).order_by(SalesforceOrg.created_at.desc()).all()
        
        # Get recent usage
        recent_usage = UsageLog.query.filter_by(user_id=user.id)\
            .order_by(UsageLog.created_at.desc())\
            .limit(5)\
            .all()
        
        # Calculate monthly stats
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        monthly_usage = UsageLog.query.filter_by(user_id=user.id)\
            .filter(UsageLog.created_at >= month_start)\
            .all()
        
        monthly_stats = {
            'total_calls': len(monthly_usage),
            'total_cost_dollars': sum(log.cost_cents for log in monthly_usage) / 100.0
        }
        
        # Basic stats for backwards compatibility
        stats = {
            'api_keys': len(active_api_keys),
            'orgs': len(orgs),
            'total_calls': len(UsageLog.query.filter_by(user_id=user.id).all()),
            'recent_usage': recent_usage
        }
        
        current_app.logger.info(f"Dashboard stats: {stats}")
        
    except Exception as e:
        current_app.logger.error(f"Error getting dashboard stats: {e}")
        api_keys = []
        orgs = []
        recent_usage = []
        monthly_stats = {
            'total_calls': 0,
            'total_cost_dollars': 0.0
        }
        stats = {
            'api_keys': 0,
            'orgs': 0,
            'total_calls': 0,
            'recent_usage': []
        }
    
    return render_template('dashboard/index.html', 
                         user=user, 
                         stats=stats,
                         api_keys=api_keys,
                         orgs=orgs,
                         recent_usage=recent_usage,
                         monthly_stats=monthly_stats)

@bp.route('/keys')
@login_required
def keys():
    """API Keys management"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    current_app.logger.info(f"Keys page accessed by: {user.email}")
    
    # Get user's API keys
    user_keys = APIKey.query.filter_by(user_id=user.id).order_by(APIKey.created_at.desc()).all()
    
    return render_template('dashboard/keys.html', user=user, api_keys=user_keys)

@bp.route('/keys/create', methods=['POST'])
@login_required
def create_key():
    """Create new API key"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    key_name = request.form.get('name', '').strip()
    if not key_name:
        flash('Key name is required', 'error')
        return redirect(url_for('dashboard.keys'))
    
    try:
        # Get default rate configuration
        rate_config = RateConfiguration.query.filter_by(is_default=True).first()
        if not rate_config:
            # Create a basic rate config if none exists
            rate_config = RateConfiguration(
                tier_name='default',
                display_name='Default',
                calls_per_hour=100,
                burst_limit=20
            )
            db.session.add(rate_config)
            db.session.flush()
        
        # Create API key
        api_key = APIKey.create_key(
            user_id=user.id,
            name=key_name,
            rate_configuration_id=rate_config.id
        )
        
        # Show the full key one time via flash message
        flash(f'API Key created successfully! Your key: {api_key.get_display_key()}', 'api_key')
        current_app.logger.info(f"API key created for user {user.email}: {api_key.key_prefix}...")
        
    except Exception as e:
        current_app.logger.error(f"Error creating API key: {e}")
        flash('Failed to create API key. Please try again.', 'error')
    
    return redirect(url_for('dashboard.keys'))

@bp.route('/keys/<key_id>/deactivate', methods=['POST'])
@login_required
def deactivate_key(key_id):
    """Deactivate an API key"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not api_key:
        flash('API key not found', 'error')
        return redirect(url_for('dashboard.keys'))
    
    try:
        api_key.deactivate()
        flash(f'API key "{api_key.name}" has been deactivated', 'success')
        current_app.logger.info(f"API key deactivated: {api_key.key_prefix}... by {user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Error deactivating API key: {e}")
        flash('Failed to deactivate API key', 'error')
    
    return redirect(url_for('dashboard.keys'))

@bp.route('/orgs')
@login_required
def orgs():
    """Salesforce organizations management"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    current_app.logger.info(f"Orgs page accessed by: {user.email}")
    
    # Get user's Salesforce orgs
    user_orgs = SalesforceOrg.query.filter_by(user_id=user.id)\
        .order_by(SalesforceOrg.created_at.desc())\
        .all()
    
    return render_template('dashboard/orgs.html', user=user, orgs=user_orgs)

@bp.route('/orgs/create', methods=['POST'])
@login_required
def create_org():
    """Initiate Salesforce OAuth flow"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    org_identifier = request.form.get('org_identifier', '').strip()
    is_sandbox = request.form.get('is_sandbox') == 'on'
    
    if not org_identifier:
        flash('Organization identifier is required', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Check if org already exists for this user
    existing_org = SalesforceOrg.query.filter_by(
        user_id=user.id,
        org_identifier=org_identifier
    ).first()
    
    if existing_org:
        flash(f'Organization "{org_identifier}" already exists', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    # Redirect to Salesforce OAuth
    oauth_url = url_for('auth.salesforce_authorize', 
                       org_identifier=org_identifier,
                       is_sandbox=is_sandbox)
    
    current_app.logger.info(f"Starting OAuth for org: {org_identifier}, sandbox: {is_sandbox}")
    return redirect(oauth_url)

@bp.route('/orgs/<org_id>/deactivate', methods=['POST'])
@login_required
def deactivate_org(org_id):
    """Deactivate a Salesforce org"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    org = SalesforceOrg.query.filter_by(id=org_id, user_id=user.id).first()
    if not org:
        flash('Organization not found', 'error')
        return redirect(url_for('dashboard.orgs'))
    
    try:
        org.deactivate()
        flash(f'Organization "{org.org_identifier}" has been disconnected', 'success')
        current_app.logger.info(f"Org deactivated: {org.org_identifier} by {user.email}")
        
    except Exception as e:
        current_app.logger.error(f"Error deactivating org: {e}")
        flash('Failed to disconnect organization', 'error')
    
    return redirect(url_for('dashboard.orgs'))

@bp.route('/usage')
@login_required
def usage():
    """Usage statistics"""
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
    
    current_app.logger.info(f"Usage page accessed by: {user.email}")
    
    # Get usage statistics
    try:
        total_calls = UsageLog.query.filter_by(user_id=user.id).count()
        successful_calls = UsageLog.query.filter_by(user_id=user.id, success=True).count()
        
        # Recent usage logs
        recent_logs = UsageLog.query.filter_by(user_id=user.id)\
            .order_by(UsageLog.created_at.desc())\
            .limit(50)\
            .all()
        
        usage_stats = {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'success_rate': round((successful_calls / total_calls * 100), 2) if total_calls > 0 else 0,
            'recent_logs': recent_logs
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting usage stats: {e}")
        usage_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'success_rate': 0,
            'recent_logs': []
        }
    
    return render_template('dashboard/usage.html', user=user, usage=usage_stats) 