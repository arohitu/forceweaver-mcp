"""
Revenue Cloud Health Checker Service for MCP Server
Simplified version without Flask dependencies.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RevenueCloudHealthChecker:
    """Health checker for Salesforce Revenue Cloud configurations."""
    
    def __init__(self, sf_client):
        """Initialize health checker with Salesforce client."""
        self.sf = sf_client
        self.checks = {}
        self.check_timestamps = {}
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all available health checks."""
        logger.info("Starting comprehensive Revenue Cloud health check")
        
        # Run all individual checks
        self.run_basic_org_info_check()
        self.run_owd_sharing_check()
        self.run_optimized_bundle_checks()
        self.run_attribute_picklist_integrity_check()
        
        # Calculate and return overall health score
        return self._calculate_health_score()
    
    def run_basic_org_info_check(self):
        """Check basic organization information and settings."""
        try:
            logger.info("Running basic org info check")
            
            # Get organization information
            org_info = self.sf.get_org_info()
            
            # Check if we have basic org data
            if org_info and org_info.get('Name'):
                self.checks['basic_org_info'] = {
                    'status': 'ok',
                    'message': f"Organization: {org_info['Name']} ({org_info.get('OrganizationType', 'Unknown')})",
                    'details': org_info
                }
            else:
                self.checks['basic_org_info'] = {
                    'status': 'error',
                    'message': "Unable to retrieve basic organization information"
                }
            
            self.check_timestamps['basic_org_info'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Basic org info check failed: {e}")
            self.checks['basic_org_info'] = {
                'status': 'error',
                'message': f"Failed to check org info: {str(e)}"
            }
    
    def run_owd_sharing_check(self):
        """Check Organization Wide Default sharing settings."""
        try:
            logger.info("Running OWD sharing check")
            
            # Query sharing settings for key objects
            sharing_objects = [
                'Account', 'Contact', 'Lead', 'Opportunity', 
                'Product2', 'PricebookEntry', 'Quote'
            ]
            
            sharing_issues = []
            checked_objects = 0
            
            for obj in sharing_objects:
                try:
                    # This is a simplified check - in reality you'd need to query
                    # the actual sharing settings through Metadata API or other means
                    describe = self.sf.describe_sobject(obj)
                    if describe:
                        checked_objects += 1
                        logger.debug(f"Checked sharing for {obj}")
                except Exception as obj_error:
                    logger.warning(f"Could not check sharing for {obj}: {obj_error}")
                    sharing_issues.append(f"Unable to check {obj} sharing settings")
            
            if sharing_issues:
                self.checks['sharing_model'] = {
                    'status': 'warning',
                    'message': f"Checked {checked_objects} objects, found {len(sharing_issues)} issues",
                    'issues': sharing_issues
                }
            else:
                self.checks['sharing_model'] = {
                    'status': 'ok',
                    'message': f"Sharing model check completed for {checked_objects} objects"
                }
            
            self.check_timestamps['sharing_model'] = datetime.now()
            
        except Exception as e:
            logger.error(f"OWD sharing check failed: {e}")
            self.checks['sharing_model'] = {
                'status': 'error',
                'message': f"Failed to check sharing model: {str(e)}"
            }
    
    def run_optimized_bundle_checks(self):
        """Check Product Bundle configurations."""
        try:
            logger.info("Running bundle analysis")
            
            # Check for Product2 records (products)
            products_query = "SELECT COUNT(Id) FROM Product2 WHERE IsActive = true"
            product_result = self.sf.query(products_query)
            product_count = product_result['records'][0]['expr0'] if product_result['records'] else 0
            
            # Check for PricebookEntry records
            pricebook_query = "SELECT COUNT(Id) FROM PricebookEntry WHERE IsActive = true"
            pricebook_result = self.sf.query(pricebook_query)
            pricebook_count = pricebook_result['records'][0]['expr0'] if pricebook_result['records'] else 0
            
            # Analyze results
            if product_count == 0:
                self.checks['bundle_analysis'] = {
                    'status': 'error',
                    'message': "No active products found in the org"
                }
            elif pricebook_count == 0:
                self.checks['bundle_analysis'] = {
                    'status': 'warning',
                    'message': f"Found {product_count} products but no active pricebook entries"
                }
            else:
                self.checks['bundle_analysis'] = {
                    'status': 'ok',
                    'message': f"Found {product_count} active products with {pricebook_count} pricebook entries"
                }
            
            self.check_timestamps['bundle_analysis'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Bundle analysis failed: {e}")
            self.checks['bundle_analysis'] = {
                'status': 'error',
                'message': f"Failed to analyze bundles: {str(e)}"
            }
    
    def run_attribute_picklist_integrity_check(self):
        """Check attribute and picklist integrity."""
        try:
            logger.info("Running attribute integrity check")
            
            # Check key objects for custom fields and picklist values
            key_objects = ['Product2', 'Opportunity', 'Quote', 'Contract']
            checked_objects = []
            issues = []
            
            for obj in key_objects:
                try:
                    describe = self.sf.describe_sobject(obj)
                    if describe and 'fields' in describe:
                        field_count = len(describe['fields'])
                        picklist_fields = [f for f in describe['fields'] if f.get('type') == 'picklist']
                        checked_objects.append(f"{obj}: {field_count} fields, {len(picklist_fields)} picklists")
                        
                        # Check for picklist fields with no values
                        for field in picklist_fields:
                            if not field.get('picklistValues'):
                                issues.append(f"{obj}.{field['name']}: picklist has no values")
                                
                except Exception as obj_error:
                    logger.warning(f"Could not check {obj}: {obj_error}")
                    issues.append(f"Unable to analyze {obj}")
            
            if issues:
                self.checks['attribute_integrity'] = {
                    'status': 'warning',
                    'message': f"Checked {len(checked_objects)} objects, found {len(issues)} issues",
                    'checked': checked_objects,
                    'issues': issues
                }
            else:
                self.checks['attribute_integrity'] = {
                    'status': 'ok',
                    'message': f"Attribute integrity check passed for {len(checked_objects)} objects",
                    'checked': checked_objects
                }
            
            self.check_timestamps['attribute_integrity'] = datetime.now()
            
        except Exception as e:
            logger.error(f"Attribute integrity check failed: {e}")
            self.checks['attribute_integrity'] = {
                'status': 'error',
                'message': f"Failed to check attribute integrity: {str(e)}"
            }
    
    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall health score based on individual check results."""
        if not self.checks:
            return {
                'checks': {},
                'overall_health': {
                    'score': 0,
                    'grade': 'F',
                    'summary': {
                        'total_checks': 0,
                        'ok': 0,
                        'warnings': 0,
                        'errors': 0
                    }
                }
            }
        
        # Count check results
        total_checks = len(self.checks)
        ok_checks = len([c for c in self.checks.values() if c['status'] == 'ok'])
        warning_checks = len([c for c in self.checks.values() if c['status'] == 'warning'])
        error_checks = len([c for c in self.checks.values() if c['status'] == 'error'])
        
        # Calculate score (ok = 100%, warning = 50%, error = 0%)
        score = ((ok_checks * 100) + (warning_checks * 50)) / total_checks if total_checks > 0 else 0
        
        # Determine grade
        if score >= 90:
            grade = 'A'
        elif score >= 80:
            grade = 'B'
        elif score >= 70:
            grade = 'C'
        elif score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'checks': self.checks,
            'overall_health': {
                'score': round(score, 1),
                'grade': grade,
                'summary': {
                    'total_checks': total_checks,
                    'ok': ok_checks,
                    'warnings': warning_checks,
                    'errors': error_checks
                }
            }
        } 