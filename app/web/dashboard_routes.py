"""
Dashboard Routes for ForceWeaver Web Interface
Main dashboard, API key management, health check history, and Salesforce org management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Customer, APIKey, SalesforceConnection, HealthCheckHistory
from app.web.forms import ConnectSalesforceForm, APIKeyForm, RunHealthCheckForm
from app.core.security import generate_api_key, hash_api_key
from app.services.health_checker_service import RevenueCloudHealthChecker
from app.services.salesforce_service import get_salesforce_api_client
import json
from datetime import datetime, timedelta
import secrets

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get user's customer and connections
    customer = current_user.customer
    
    # Dashboard statistics
    stats = {
        'has_salesforce_connection': bool(customer and customer.salesforce_connection),
        'has_api_key': bool(customer and customer.api_key),
        'total_health_checks': 0,
        'last_health_check': None,
        'api_key_last_used': None
    }
    
    if customer:
        # Get health check statistics
        stats['total_health_checks'] = HealthCheckHistory.query.filter_by(
            user_id=current_user.id,
            customer_id=customer.id
        ).count()
        
        # Get last health check
        last_check = HealthCheckHistory.query.filter_by(
            user_id=current_user.id,
            customer_id=customer.id
        ).order_by(HealthCheckHistory.created_at.desc()).first()
        
        if last_check:
            stats['last_health_check'] = last_check.created_at
        
        # Get API key last used
        if customer.api_key:
            stats['api_key_last_used'] = customer.api_key.last_used
    
    return render_template('dashboard/index.html', stats=stats, customer=customer)

@dashboard_bp.route('/salesforce')
@login_required
def salesforce():
    """Salesforce connection management page"""
    customer = current_user.customer
    connection = customer.salesforce_connection if customer else None
    
    form = ConnectSalesforceForm()
    
    return render_template('dashboard/salesforce.html', 
                         customer=customer, 
                         connection=connection,
                         form=form)

@dashboard_bp.route('/connect-salesforce', methods=['POST'])
@login_required
def connect_salesforce():
    """Initiate Salesforce OAuth connection"""
    form = ConnectSalesforceForm()
    
    if form.validate_on_submit():
        # Store org nickname in session for use after OAuth
        from flask import session
        session['org_nickname'] = form.org_nickname.data
        session['user_id_for_oauth'] = current_user.id
        
        # Redirect to Salesforce OAuth initiation (reuse existing API route)
        return redirect(url_for('auth.initiate_salesforce_auth', email=current_user.email))
    
    flash('Please provide a valid organization nickname', 'error')
    return redirect(url_for('dashboard.salesforce'))

@dashboard_bp.route('/disconnect-salesforce', methods=['POST'])
@login_required
def disconnect_salesforce():
    """Disconnect Salesforce org"""
    customer = current_user.customer
    
    if customer and customer.salesforce_connection:
        # Remove the connection
        db.session.delete(customer.salesforce_connection)
        
        # Also remove API key for security
        if customer.api_key:
            db.session.delete(customer.api_key)
        
        db.session.commit()
        flash('Salesforce organization disconnected successfully', 'success')
    else:
        flash('No Salesforce connection found', 'error')
    
    return redirect(url_for('dashboard.salesforce'))

@dashboard_bp.route('/api-keys')
@login_required
def api_keys():
    """API key management page"""
    customer = current_user.customer
    form = APIKeyForm()
    
    return render_template('dashboard/api_keys.html', 
                         customer=customer,
                         form=form)

@dashboard_bp.route('/create-api-key', methods=['POST'])
@login_required
def create_api_key():
    """Create new API key"""
    form = APIKeyForm()
    
    if not current_user.customer or not current_user.customer.salesforce_connection:
        flash('Please connect a Salesforce organization first', 'error')
        return redirect(url_for('dashboard.salesforce'))
    
    customer = current_user.customer
    
    # Check if API key already exists
    if customer.api_key:
        flash('API key already exists. Revoke the existing key first.', 'error')
        return redirect(url_for('dashboard.api_keys'))
    
    if form.validate_on_submit():
        # Generate new API key
        api_key_value = generate_api_key()
        
        api_key = APIKey(
            hashed_key=hash_api_key(api_key_value),
            customer_id=customer.id,
            name=form.key_name.data
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        # Show the API key once (store in session temporarily)
        from flask import session
        session['new_api_key'] = api_key_value
        session['new_api_key_name'] = form.key_name.data
        
        flash('API key created successfully!', 'success')
        return redirect(url_for('dashboard.show_api_key'))
    
    flash('Please provide a valid API key name', 'error')
    return redirect(url_for('dashboard.api_keys'))

@dashboard_bp.route('/show-api-key')
@login_required
def show_api_key():
    """Show newly created API key (one time only)"""
    from flask import session
    
    api_key = session.pop('new_api_key', None)
    api_key_name = session.pop('new_api_key_name', None)
    
    if not api_key:
        flash('No new API key to display', 'error')
        return redirect(url_for('dashboard.api_keys'))
    
    return render_template('dashboard/show_api_key.html', 
                         api_key=api_key,
                         api_key_name=api_key_name)

@dashboard_bp.route('/revoke-api-key', methods=['POST'])
@login_required
def revoke_api_key():
    """Revoke existing API key"""
    customer = current_user.customer
    
    if customer and customer.api_key:
        db.session.delete(customer.api_key)
        db.session.commit()
        flash('API key revoked successfully', 'success')
    else:
        flash('No API key found to revoke', 'error')
    
    return redirect(url_for('dashboard.api_keys'))

@dashboard_bp.route('/health-checks')
@login_required
def health_checks():
    """Health check history page"""
    customer = current_user.customer
    
    # Get health check history
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    history = None
    if customer:
        history = HealthCheckHistory.query.filter_by(
            user_id=current_user.id,
            customer_id=customer.id
        ).order_by(HealthCheckHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    form = RunHealthCheckForm()
    
    return render_template('dashboard/health_checks.html', 
                         customer=customer,
                         history=history,
                         form=form)

@dashboard_bp.route('/run-health-check', methods=['POST'])
@login_required
def run_health_check():
    """Run a new health check"""
    customer = current_user.customer
    
    if not customer or not customer.salesforce_connection:
        flash('Please connect a Salesforce organization first', 'error')
        return redirect(url_for('dashboard.salesforce'))
    
    try:
        # Get Salesforce client
        sf_client = get_salesforce_api_client(customer.salesforce_connection)
        
        # Run health check
        checker = RevenueCloudHealthChecker(sf_client)
        start_time = datetime.utcnow()
        results = checker.run_all_checks()
        end_time = datetime.utcnow()
        
        execution_time = int((end_time - start_time).total_seconds())
        
        # Store results in history
        history_entry = HealthCheckHistory(
            user_id=current_user.id,
            customer_id=customer.id,
            salesforce_org_id=customer.salesforce_connection.salesforce_org_id,
            overall_health_score=results.get('overall_health_score'),
            overall_health_grade=results.get('overall_health_grade'),
            checks_performed=results.get('checks_performed'),
            checks_passed=len([c for c in results.get('checks', {}).values() if c.get('status') == 'passed']),
            checks_failed=len([c for c in results.get('checks', {}).values() if c.get('status') == 'failed']),
            checks_warnings=len([c for c in results.get('checks', {}).values() if c.get('status') == 'warning']),
            full_results=json.dumps(results),
            execution_time_seconds=execution_time,
            triggered_by='web_dashboard'
        )
        
        db.session.add(history_entry)
        db.session.commit()
        
        flash(f'Health check completed successfully! Score: {results.get("overall_health_score", "N/A")}', 'success')
        return redirect(url_for('dashboard.health_check_detail', check_id=history_entry.id))
        
    except Exception as e:
        current_app.logger.error(f"Health check failed for user {current_user.id}: {e}")
        flash('Health check failed. Please try again later.', 'error')
        return redirect(url_for('dashboard.health_checks'))

@dashboard_bp.route('/health-check/<int:check_id>')
@login_required
def health_check_detail(check_id):
    """Show detailed health check results"""
    check = HealthCheckHistory.query.filter_by(
        id=check_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Parse JSON results
    results = {}
    try:
        results = json.loads(check.full_results)
    except:
        results = {}
    
    return render_template('dashboard/health_check_detail.html', 
                         check=check,
                         results=results)

@dashboard_bp.route('/settings')
@login_required
def settings():
    """User settings page"""
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/api/dashboard-stats')
@login_required
def api_dashboard_stats():
    """API endpoint for dashboard statistics (AJAX)"""
    customer = current_user.customer
    
    stats = {
        'has_connection': bool(customer and customer.salesforce_connection),
        'has_api_key': bool(customer and customer.api_key),
        'total_checks': 0,
        'checks_this_month': 0,
        'avg_health_score': 0
    }
    
    if customer:
        # Total checks
        stats['total_checks'] = HealthCheckHistory.query.filter_by(
            user_id=current_user.id,
            customer_id=customer.id
        ).count()
        
        # Checks this month
        first_day_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stats['checks_this_month'] = HealthCheckHistory.query.filter(
            HealthCheckHistory.user_id == current_user.id,
            HealthCheckHistory.customer_id == customer.id,
            HealthCheckHistory.created_at >= first_day_month
        ).count()
        
        # Average health score
        avg_score = db.session.query(db.func.avg(HealthCheckHistory.overall_health_score)).filter(
            HealthCheckHistory.user_id == current_user.id,
            HealthCheckHistory.customer_id == customer.id,
            HealthCheckHistory.overall_health_score.isnot(None)
        ).scalar()
        
        stats['avg_health_score'] = round(avg_score or 0, 1)
    
    return jsonify(stats) 