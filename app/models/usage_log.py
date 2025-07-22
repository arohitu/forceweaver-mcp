"""
Usage Log model for tracking API usage and billing
"""
import uuid
from datetime import datetime
from app import db

class UsageLog(db.Model):
    """Usage log model for tracking API calls and billing"""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    api_key_id = db.Column(db.String(36), db.ForeignKey('api_keys.id'), nullable=False)
    salesforce_org_id = db.Column(db.String(36), db.ForeignKey('salesforce_orgs.id'))
    
    # API call details
    tool_name = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(50))  # For future REST API support
    endpoint = db.Column(db.String(255))  # For future REST API support
    
    # Execution details
    execution_time_ms = db.Column(db.Integer)
    success = db.Column(db.Boolean, nullable=False, default=True)
    error_message = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    
    # Billing information
    cost_cents = db.Column(db.Integer, default=1)  # Cost in cents (1 cent = $0.01)
    
    # Metadata
    user_agent = db.Column(db.String(255))
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    request_id = db.Column(db.String(50))  # For tracing
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    api_key = db.relationship('APIKey', backref='usage_logs')
    salesforce_org = db.relationship('SalesforceOrg', backref='usage_logs')
    
    def __init__(self, user_id, api_key_id, tool_name, success=True, 
                 execution_time_ms=None, error_message=None, cost_cents=1,
                 salesforce_org_id=None, user_agent=None, ip_address=None):
        self.user_id = user_id
        self.api_key_id = api_key_id
        self.tool_name = tool_name
        self.success = success
        self.execution_time_ms = execution_time_ms
        self.error_message = error_message
        self.cost_cents = cost_cents
        self.salesforce_org_id = salesforce_org_id
        self.user_agent = user_agent
        self.ip_address = ip_address
        self.request_id = str(uuid.uuid4())[:8]  # Short request ID
    
    def __repr__(self):
        return f'<UsageLog {self.tool_name} for {self.user_id} at {self.created_at}>'
    
    def to_dict(self):
        """Convert usage log to dictionary"""
        return {
            'id': self.id,
            'tool_name': self.tool_name,
            'execution_time_ms': self.execution_time_ms,
            'success': self.success,
            'error_message': self.error_message,
            'cost_cents': self.cost_cents,
            'created_at': self.created_at.isoformat(),
            'request_id': self.request_id,
            'salesforce_org_id': self.salesforce_org_id
        }
    
    @classmethod
    def log_usage(cls, user_id, api_key_id, tool_name, success=True, 
                  execution_time_ms=None, error_message=None, cost_cents=1,
                  salesforce_org_id=None, user_agent=None, ip_address=None):
        """Create and save a usage log entry"""
        usage_log = cls(
            user_id=user_id,
            api_key_id=api_key_id,
            tool_name=tool_name,
            success=success,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            cost_cents=cost_cents,
            salesforce_org_id=salesforce_org_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.session.add(usage_log)
        db.session.commit()
        return usage_log
    
    @classmethod
    def get_user_usage(cls, user_id, start_date=None, end_date=None, limit=100):
        """Get usage logs for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_usage_stats(cls, user_id, start_date=None, end_date=None):
        """Get usage statistics for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        logs = query.all()
        
        total_calls = len(logs)
        successful_calls = len([log for log in logs if log.success])
        failed_calls = total_calls - successful_calls
        total_cost_cents = sum(log.cost_cents for log in logs)
        
        # Tool usage breakdown
        tool_usage = {}
        for log in logs:
            tool_name = log.tool_name
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {'count': 0, 'cost_cents': 0, 'success': 0, 'failed': 0}
            
            tool_usage[tool_name]['count'] += 1
            tool_usage[tool_name]['cost_cents'] += log.cost_cents
            
            if log.success:
                tool_usage[tool_name]['success'] += 1
            else:
                tool_usage[tool_name]['failed'] += 1
        
        # Average execution time (only for successful calls)
        successful_logs = [log for log in logs if log.success and log.execution_time_ms]
        avg_execution_time = None
        if successful_logs:
            avg_execution_time = sum(log.execution_time_ms for log in successful_logs) / len(successful_logs)
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'success_rate': successful_calls / total_calls * 100 if total_calls > 0 else 0,
            'total_cost_cents': total_cost_cents,
            'total_cost_dollars': total_cost_cents / 100,
            'avg_execution_time_ms': avg_execution_time,
            'tool_usage': tool_usage,
            'period_start': start_date.isoformat() if start_date else None,
            'period_end': end_date.isoformat() if end_date else None
        }
    
    @classmethod
    def get_monthly_usage(cls, user_id, year=None, month=None):
        """Get usage for a specific month"""
        if not year or not month:
            now = datetime.utcnow()
            year = year or now.year
            month = month or now.month
        
        # Start of month
        from datetime import date
        start_date = datetime(year, month, 1)
        
        # Start of next month
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        return cls.get_usage_stats(user_id, start_date, end_date)
    
    @classmethod
    def cleanup_old_logs(cls, days_to_keep=365):
        """Clean up usage logs older than specified days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        old_logs = cls.query.filter(cls.created_at < cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        
        db.session.commit()
        return count 