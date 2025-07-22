"""
Revenue Cloud Health Checker
Performs comprehensive health checks on Salesforce Revenue Cloud setup
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from salesforce_client import SalesforceClient

logger = logging.getLogger(__name__)

class RevenueCloudHealthChecker:
    """Performs health checks on Salesforce Revenue Cloud configuration"""
    
    def __init__(self, sf_client: SalesforceClient):
        self.sf = sf_client
    
    async def run_checks(self, check_types: List[str]) -> Dict[str, Any]:
        """Run specified health checks"""
        results = {}
        
        # Available check methods
        check_methods = {
            "basic_org_info": self._check_basic_org_info,
            "sharing_model": self._check_sharing_model,
            "bundle_analysis": self._check_bundle_analysis,
            "data_integrity": self._check_data_integrity,
            "performance_metrics": self._check_performance_metrics,
            "security_audit": self._check_security_audit
        }
        
        # Run each requested check
        for check_type in check_types:
            if check_type in check_methods:
                try:
                    logger.info(f"Running check: {check_type}")
                    results[check_type] = await check_methods[check_type]()
                except Exception as e:
                    logger.error(f"Check {check_type} failed: {e}")
                    results[check_type] = {
                        "status": "error",
                        "score": 0,
                        "error": str(e),
                        "details": [f"Check failed: {e}"]
                    }
            else:
                results[check_type] = {
                    "status": "error",
                    "score": 0,
                    "error": f"Unknown check type: {check_type}",
                    "details": [f"Check type '{check_type}' is not supported"]
                }
        
        # Calculate overall score
        if results:
            scores = [result.get("score", 0) for result in results.values() if isinstance(result, dict)]
            overall_score = sum(scores) // len(scores) if scores else 0
            results["overall_score"] = overall_score
        
        return results
    
    async def _check_basic_org_info(self) -> Dict[str, Any]:
        """Check basic organization information and setup"""
        try:
            # Get organization info
            org_query = """
                SELECT Id, Name, OrganizationType, IsSandbox, InstanceName, 
                       LanguageLocaleKey, TimeZoneSidKey, DefaultCurrencyIsoCode,
                       UsersCount, TrialExpirationDate
                FROM Organization
                LIMIT 1
            """
            org_result = await self.sf.query(org_query)
            
            if not org_result.get('records'):
                return {
                    "status": "error",
                    "score": 0,
                    "details": ["Could not retrieve organization information"]
                }
            
            org = org_result['records'][0]
            details = []
            recommendations = []
            score = 80  # Base score
            
            # Basic org details
            details.append(f"Organization: {org['Name']}")
            details.append(f"Type: {org['OrganizationType']}")
            details.append(f"Instance: {org['InstanceName']}")
            details.append(f"Users: {org.get('UsersCount', 'Unknown')}")
            
            # Check if it's a trial org
            if org.get('TrialExpirationDate'):
                details.append(f"⚠️ Trial org expires: {org['TrialExpirationDate']}")
                recommendations.append("Consider upgrading from trial to production org")
                score -= 10
            
            # Check currency setup
            if not org.get('DefaultCurrencyIsoCode'):
                recommendations.append("Set up default currency for proper revenue tracking")
                score -= 5
            else:
                details.append(f"Currency: {org['DefaultCurrencyIsoCode']}")
            
            # Check user count
            user_count = org.get('UsersCount', 0)
            if user_count > 100:
                details.append("✅ Large organization with good user adoption")
                score += 10
            elif user_count < 5:
                recommendations.append("Consider onboarding more users to maximize ROI")
                score -= 5
            
            return {
                "status": "healthy" if score >= 70 else "warning" if score >= 50 else "critical",
                "score": score,
                "details": details,
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Basic org info check failed: {e}")
            return {
                "status": "error",
                "score": 0,
                "details": [f"Failed to retrieve org info: {e}"]
            }
    
    async def _check_sharing_model(self) -> Dict[str, Any]:
        """Check organization-wide defaults and sharing model"""
        try:
            # Check key objects' sharing settings
            sharing_objects = ['Account', 'Contact', 'Opportunity', 'Lead', 'Case']
            details = []
            recommendations = []
            score = 90  # Start with high score
            
            for obj_name in sharing_objects:
                try:
                    # Query organization-wide defaults
                    owd_query = f"""
                        SELECT SobjectType, DefaultAccountAccess, DefaultContactAccess,
                               DefaultOpportunityAccess, DefaultLeadAccess, DefaultCaseAccess
                        FROM OrganizationWideDefault 
                        WHERE SobjectType = '{obj_name}'
                        LIMIT 1
                    """
                    
                    owd_result = await self.sf.query(owd_query)
                    
                    if owd_result.get('records'):
                        record = owd_result['records'][0]
                        
                        # Check access levels
                        access_field = f"Default{obj_name}Access"
                        access_level = record.get(access_field, 'Unknown')
                        
                        if access_level == 'Public':
                            details.append(f"⚠️ {obj_name}: Public access (consider if appropriate)")
                            recommendations.append(f"Review if {obj_name} should have public access for security")
                            score -= 5
                        elif access_level == 'Private':
                            details.append(f"✅ {obj_name}: Private access (secure)")
                        else:
                            details.append(f"{obj_name}: {access_level} access")
                
                except Exception as e:
                    details.append(f"Could not check {obj_name} sharing: {e}")
                    score -= 2
            
            # Check for sharing rules
            sharing_rules_query = "SELECT COUNT() FROM SharingRule"
            try:
                sharing_count = await self.sf.query(sharing_rules_query)
                rule_count = sharing_count.get('totalSize', 0)
                
                if rule_count > 0:
                    details.append(f"✅ {rule_count} sharing rules configured")
                else:
                    details.append("No custom sharing rules found")
                    recommendations.append("Consider setting up sharing rules for better data access control")
                    score -= 5
            
            except Exception:
                details.append("Could not check sharing rules")
            
            return {
                "status": "healthy" if score >= 80 else "warning" if score >= 60 else "critical",
                "score": max(score, 0),
                "details": details,
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Sharing model check failed: {e}")
            return {
                "status": "error", 
                "score": 0,
                "details": [f"Sharing model check failed: {e}"]
            }
    
    async def _check_bundle_analysis(self) -> Dict[str, Any]:
        """Check Revenue Cloud product bundle configuration"""
        try:
            details = []
            recommendations = []
            score = 75  # Base score
            
            # Check if Revenue Cloud objects exist
            revenue_objects = [
                'Product2', 'PricebookEntry', 'Quote', 'QuoteLineItem',
                'Contract', 'Order', 'OrderItem'
            ]
            
            object_counts = {}
            
            for obj in revenue_objects:
                try:
                    count_query = f"SELECT COUNT() FROM {obj} LIMIT 1"
                    result = await self.sf.query(count_query)
                    count = result.get('totalSize', 0)
                    object_counts[obj] = count
                    
                    if count > 0:
                        details.append(f"✅ {obj}: {count} records")
                    else:
                        details.append(f"⚠️ {obj}: No records found")
                        
                except Exception as e:
                    details.append(f"❌ {obj}: Could not access ({e})")
                    score -= 5
            
            # Check product setup
            if object_counts.get('Product2', 0) == 0:
                recommendations.append("Set up products in your catalog for Revenue Cloud functionality")
                score -= 20
            
            # Check pricebook setup
            if object_counts.get('PricebookEntry', 0) == 0:
                recommendations.append("Configure pricebook entries for your products")
                score -= 15
            
            # Check if quotes are being used
            if object_counts.get('Quote', 0) > 0:
                details.append("✅ Quote functionality is being utilized")
                score += 5
            else:
                recommendations.append("Consider using Quote functionality for better revenue tracking")
            
            # Check order management
            if object_counts.get('Order', 0) > 0:
                details.append("✅ Order management is active")
                score += 5
            else:
                recommendations.append("Enable Order management for complete revenue lifecycle")
            
            return {
                "status": "healthy" if score >= 70 else "warning" if score >= 50 else "critical",
                "score": max(score, 0),
                "details": details,
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Bundle analysis failed: {e}")
            return {
                "status": "error",
                "score": 0,
                "details": [f"Bundle analysis failed: {e}"]
            }
    
    async def _check_data_integrity(self) -> Dict[str, Any]:
        """Check data integrity and quality"""
        try:
            details = []
            recommendations = []
            score = 85  # Start with good score
            
            # Check for duplicate accounts
            duplicate_accounts_query = """
                SELECT COUNT() FROM Account 
                WHERE Name IN (
                    SELECT Name FROM Account 
                    GROUP BY Name 
                    HAVING COUNT(Id) > 1
                )
            """
            
            try:
                dup_result = await self.sf.query(duplicate_accounts_query)
                dup_count = dup_result.get('totalSize', 0)
                
                if dup_count > 0:
                    details.append(f"⚠️ {dup_count} potential duplicate accounts found")
                    recommendations.append("Review and merge duplicate accounts to maintain data quality")
                    score -= 10
                else:
                    details.append("✅ No obvious duplicate accounts detected")
            
            except Exception:
                details.append("Could not check for duplicate accounts")
            
            # Check for missing required fields
            try:
                # Check opportunities without close dates
                missing_close_date_query = "SELECT COUNT() FROM Opportunity WHERE CloseDate = null"
                missing_result = await self.sf.query(missing_close_date_query)
                missing_count = missing_result.get('totalSize', 0)
                
                if missing_count > 0:
                    details.append(f"⚠️ {missing_count} opportunities missing close dates")
                    recommendations.append("Ensure all opportunities have proper close dates")
                    score -= 5
                else:
                    details.append("✅ All opportunities have close dates")
            
            except Exception:
                details.append("Could not check opportunity close dates")
            
            # Check for orphaned records
            try:
                orphaned_contacts_query = "SELECT COUNT() FROM Contact WHERE AccountId = null"
                orphaned_result = await self.sf.query(orphaned_contacts_query)
                orphaned_count = orphaned_result.get('totalSize', 0)
                
                if orphaned_count > 0:
                    details.append(f"⚠️ {orphaned_count} contacts not associated with accounts")
                    recommendations.append("Associate orphaned contacts with appropriate accounts")
                    score -= 5
                else:
                    details.append("✅ All contacts are properly associated with accounts")
            
            except Exception:
                details.append("Could not check for orphaned contacts")
            
            return {
                "status": "healthy" if score >= 75 else "warning" if score >= 50 else "critical",
                "score": max(score, 0),
                "details": details,
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            return {
                "status": "error",
                "score": 0,
                "details": [f"Data integrity check failed: {e}"]
            }
    
    async def _check_performance_metrics(self) -> Dict[str, Any]:
        """Check performance metrics and API usage"""
        return {
            "status": "info",
            "score": 70,
            "details": [
                "Performance metrics check is a premium feature",
                "This would analyze API call patterns, response times, and system performance"
            ],
            "recommendations": [
                "Upgrade to premium ForceWeaver plan for detailed performance analytics"
            ]
        }
    
    async def _check_security_audit(self) -> Dict[str, Any]:
        """Perform security audit"""
        return {
            "status": "info", 
            "score": 70,
            "details": [
                "Security audit is a premium feature",
                "This would check user permissions, field-level security, and access patterns"
            ],
            "recommendations": [
                "Upgrade to premium ForceWeaver plan for comprehensive security auditing"
            ]
        } 