import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

class HealthCheckResult:
    """Class to represent the result of a health check."""
    def __init__(self, check_name, status, message, details=None, severity="info"):
        self.check_name = check_name
        self.status = status  # "passed", "failed", "warning", "info"
        self.message = message
        self.details = details or []
        self.severity = severity
        self.timestamp = datetime.now()

class RevenueCloudHealthChecker:
    """Comprehensive health checker for Salesforce Revenue Cloud configurations."""
    
    def __init__(self, sf_client, session_id=None):
        self.sf = sf_client
        self.results = []
        self.session_id = session_id
        self.total_checks = 4  # org info, OWD sharing, combined bundle checks, and attribute picklist integrity
        self.current_check = 0
        
    def update_progress(self, check_name, status="in_progress", percentage=None):
        """Update progress for the current session."""
        if self.session_id:
            if percentage is None:
                percentage = (self.current_check / self.total_checks) * 100
            
            # In a real implementation, you might store this in Redis or a database
            # For now, we'll just log it
            logger.info(f"Progress: {check_name} - {status} ({percentage:.1f}%)")
        
    def add_result(self, check_name, status, message, details=None, severity="info"):
        """Add a health check result."""
        result = HealthCheckResult(check_name, status, message, details, severity)
        self.results.append(result)
        return result
        
    def get_results_summary(self):
        """Get a summary of all health check results."""
        total_checks = len(self.results)
        passed = len([r for r in self.results if r.status == "passed"])
        failed = len([r for r in self.results if r.status == "failed"])
        warnings = len([r for r in self.results if r.status == "warning"])
        info = len([r for r in self.results if r.status == "info"])
        
        return {
            "total_checks": total_checks,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "info": info,
            "overall_status": "failed" if failed > 0 else "warning" if warnings > 0 else "passed"
        }
    
    def run_basic_org_info_check(self):
        """Check basic organization information."""
        self.current_check += 1
        self.update_progress("Basic Organization Info", "in_progress")
        
        try:
            # Get organization info
            org_query = "SELECT Id, Name, OrganizationType, InstanceName, IsSandbox, TrialExpirationDate FROM Organization LIMIT 1"
            org_result = self.sf.query(org_query)
            
            if org_result['totalSize'] > 0:
                org_info = org_result['records'][0]
                details = [
                    f"Organization: {org_info['Name']}",
                    f"Type: {org_info['OrganizationType']}",
                    f"Instance: {org_info['InstanceName']}",
                    f"Sandbox: {'Yes' if org_info['IsSandbox'] else 'No'}"
                ]
                
                if org_info.get('TrialExpirationDate'):
                    details.append(f"Trial Expiration: {org_info['TrialExpirationDate']}")
                
                self.add_result(
                    "Basic Organization Info",
                    "passed",
                    "Successfully retrieved organization information",
                    details,
                    "info"
                )
            else:
                self.add_result(
                    "Basic Organization Info",
                    "failed",
                    "Could not retrieve organization information",
                    severity="error"
                )
                
        except Exception as e:
            self.add_result(
                "Basic Organization Info",
                "failed",
                f"Error retrieving organization information: {str(e)}",
                severity="error"
            )
        
        self.update_progress("Basic Organization Info", "completed")
    
    def run_owd_sharing_check(self):
        """Check Organization-Wide Default sharing settings for PCM objects."""
        self.current_check += 1
        self.update_progress("OWD Sharing Settings", "in_progress")
        
        try:
            # PCM objects to check
            pcm_objects = [
                'Product2', 'Catalog', 'Category', 'AttributeDefinition', 'AttributeCategory',
                'ProductClassification', 'ProductSellingModel', 'Pricebook2', 'PricebookEntry',
                'ProductQualificationRule', 'ProductDisqualificationRule', 'DecisionMatrix', 'ExpressionSet'
            ]
            
            # Query for sharing settings
            objects_quoted = [f"'{obj}'" for obj in pcm_objects]
            sharing_query = f"""
                SELECT QualifiedApiName, InternalSharingModel, Label
                FROM EntityDefinition 
                WHERE QualifiedApiName IN ({','.join(objects_quoted)})
            """
            
            sharing_results = self.sf.query_all(sharing_query)
            
            if sharing_results['totalSize'] == 0:
                self.add_result(
                    "OWD Sharing Settings Check",
                    "failed",
                    "No sharing settings found for PCM objects",
                    severity="error"
                )
                return
            
            # Process results
            passed_objects = []
            failed_objects = []
            missing_objects = []
            details = []
            
            found_objects = {record['QualifiedApiName']: record for record in sharing_results['records']}
            
            for obj in pcm_objects:
                if obj in found_objects:
                    record = found_objects[obj]
                    sharing_model = record['InternalSharingModel']
                    
                    # Acceptable values: ReadWrite (Public Read/Write), Read (Public Read Only)
                    if sharing_model in ['ReadWrite', 'Read']:
                        passed_objects.append(obj)
                        status_emoji = "✅"
                        status_text = "PASS"
                    else:
                        failed_objects.append(obj)
                        status_emoji = "❌"
                        status_text = "FAIL"
                    
                    # Map sharing model to user-friendly text
                    sharing_display = {
                        'ReadWrite': 'Public Read/Write',
                        'Read': 'Public Read Only',
                        'Private': 'Private'
                    }.get(sharing_model, sharing_model)
                    
                    details.append(f"{status_emoji} {obj}: {sharing_display} ({status_text})")
                else:
                    missing_objects.append(obj)
                    details.append(f"⚠️ {obj}: Object not found")
            
            # Add recommendations for failed objects
            if failed_objects:
                details.append("🔧 Recommendations:")
                details.append("Failed objects should be set to 'Public Read Only' or 'Public Read/Write'")
                details.append("Navigate to: Setup → Security → Sharing Settings → Organization-Wide Defaults")
                for obj in failed_objects:
                    details.append(f"    Change {obj} from 'Private' to 'Public Read Only'")
            
            # Determine overall status
            if len(failed_objects) == 0:
                if len(missing_objects) == 0:
                    status = "passed"
                    message = f"All {len(passed_objects)} PCM objects have proper OWD sharing settings"
                else:
                    status = "warning"
                    message = f"{len(passed_objects)} objects passed, {len(missing_objects)} objects not found"
            else:
                status = "failed"
                message = f"{len(failed_objects)} objects have restrictive sharing settings that may prevent access"
            
            severity = "info" if status == "passed" else "warning" if status == "warning" else "error"
            
            self.add_result(
                "OWD Sharing Settings Check",
                status,
                message,
                details,
                severity
            )
            
        except Exception as e:
            self.add_result(
                "OWD Sharing Settings Check",
                "failed",
                f"Error checking OWD sharing settings: {str(e)}",
                severity="error"
            )
        
        self.update_progress("OWD Sharing Settings", "completed")
    
    def run_optimized_bundle_checks(self):
        """Run both bundle analysis and attribute override checks with optimized queries."""
        self.current_check += 1
        self.update_progress("Bundle Analysis & Attribute Override", "in_progress")
        
        try:
            # Single combined query for all bundle data
            bundle_query = """
                SELECT Id, Name, Type 
                FROM Product2 
                WHERE Type = 'Bundle' 
                AND IsActive = true
            """
            
            bundle_results = self.sf.query_all(bundle_query)
            
            if bundle_results['totalSize'] == 0:
                # Both checks pass with no bundles
                self.add_result(
                    "Bundle Analysis",
                    "info",
                    "No active bundle products found in the org",
                    severity="info"
                )
                self.add_result(
                    "Attribute Override Check",
                    "passed",
                    "No bundle products found in the org.",
                    severity="info"
                )
                return
            
            # Single query for all ProductRelatedComponent data
            component_query = """
                SELECT Id, ParentProductId, ChildProductId, 
                       ParentProduct.Name, ParentProduct.Type,
                       ChildProduct.Name, ChildProduct.Type,
                       sequence, Quantity
                FROM ProductRelatedComponent 
                WHERE ParentProductId != NULL AND ChildProductId != NULL
            """
            
            component_results = self.sf.query_all(component_query)
            
            # Build parent-child relationship map (used by both checks)
            parent_child_map = {}
            for component in component_results['records']:
                parent_id = component['ParentProductId']
                if parent_id not in parent_child_map:
                    parent_child_map[parent_id] = []
                parent_child_map[parent_id].append(component)
            
            # Process both checks in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both tasks
                bundle_analysis_future = executor.submit(
                    self._process_bundle_analysis, 
                    bundle_results['records'], 
                    parent_child_map
                )
                
                attribute_override_future = executor.submit(
                    self._process_attribute_override_check, 
                    bundle_results['records'], 
                    parent_child_map
                )
                
                # Wait for both to complete
                bundle_analysis_future.result()
                attribute_override_future.result()
            
        except Exception as e:
            self.add_result(
                "Bundle Analysis",
                "failed",
                f"Error in bundle analysis: {str(e)}",
                severity="error"
            )
            self.add_result(
                "Attribute Override Check",
                "failed",
                f"Error in attribute override check: {str(e)}",
                severity="error"
            )
        
        self.update_progress("Bundle Analysis & Attribute Override", "completed")
    
    def _process_bundle_analysis(self, bundle_products, parent_child_map):
        """Process bundle analysis logic."""
        try:
            # Analyze each bundle
            analysis_results = []
            depth_violations = []
            component_violations = []
            warnings = []
            
            for bundle in bundle_products:
                bundle_id = bundle['Id']
                bundle_name = bundle['Name']
                
                # Analyze hierarchy depth and component count
                max_depth, total_components = self._analyze_bundle_hierarchy(
                    bundle_id, parent_child_map, current_depth=1
                )
                
                # Check for violations
                if max_depth > 5:
                    depth_violations.append({
                        'name': bundle_name,
                        'depth': max_depth,
                        'limit': 5
                    })
                
                if total_components > 200:
                    component_violations.append({
                        'name': bundle_name,
                        'components': total_components,
                        'limit': 200
                    })
                elif total_components > 180:  # Warning threshold
                    warnings.append({
                        'name': bundle_name,
                        'components': total_components,
                        'limit': 200
                    })
                
                analysis_results.append({
                    'name': bundle_name,
                    'depth': max_depth,
                    'components': total_components
                })
            
            # Detect circular bundle dependencies
            cycles = self._detect_bundle_cycles(bundle_products, parent_child_map)
            
            # Generate detailed results
            details = []
            details.append(f"Analyzed {len(bundle_products)} bundle products")
            
            # Add summary statistics and structured sections
            if analysis_results:
                max_depth_found = max(result['depth'] for result in analysis_results)
                max_components_found = max(result['components'] for result in analysis_results)
                
                details.append("📊 Summary Statistics:")
                details.append(f"Maximum components found: {max_components_found}")
                
                # Find bundle with largest components
                largest_bundle = max(analysis_results, key=lambda x: x['components'])
                details.append(f"Bundle with most components: {largest_bundle['name']} ({largest_bundle['components']} components)")
                
                # Section 1: Nested Depth
                details.append("📏 Nested Depth:")
                details.append(f"Maximum depth found: {max_depth_found} levels")
                
                # Section 2: Circular Bundle Dependencies
                details.append("🔄 Circular Bundle Dependencies:")
                if cycles:
                    details.append(f"⚠️ {len(cycles)} circular dependencies detected:")
                    for i, cycle in enumerate(cycles, 1):
                        details.append(f"   {i}. {cycle['cycle_path']}")
                        details.append(f"      Cycle length: {cycle['cycle_length']} bundles")
                else:
                    details.append("✅ No circular dependencies found")
                
                # Section 3: Large bundle check
                details.append("📋 Large Bundle Check:")
                
                # Sort bundles by component count (descending)
                sorted_bundles = sorted(analysis_results, key=lambda x: x['components'], reverse=True)
                
                # Add bundle details
                for bundle in sorted_bundles:
                    details.append(f"   • {bundle['name']}: {bundle['components']} components")
            
            # Report depth violations
            if depth_violations:
                details.append("❌ Depth Limit Violations (> 5 levels):")
                for violation in depth_violations:
                    details.append(f"    {violation['name']}: {violation['depth']} levels")
            
            # Report component violations
            if component_violations:
                details.append("❌ Component Count Violations (> 200 components):")
                for violation in component_violations:
                    details.append(f"    {violation['name']}: {violation['components']} components")
            
            # Report warnings
            if warnings:
                details.append("⚠️ Approaching Component Limit (> 180 components):")
                for warning in warnings:
                    details.append(f"    {warning['name']}: {warning['components']}/200 components")
            
            # Add recommendations
            if depth_violations or component_violations or cycles:
                details.append("🔧 Recommendations:")
                if cycles:
                    details.append("    CRITICAL: Remove circular dependencies immediately to prevent infinite loops")
                    details.append("    Review bundle relationships and restructure to avoid cycles")
                    details.append("    Consider using alternative design patterns instead of circular references")
                if depth_violations:
                    details.append("    Review bundle hierarchy to reduce nesting levels")
                    details.append("    Consider flattening deeply nested structures")
                if component_violations:
                    details.append("    Split large bundles into smaller sub-bundles")
                    details.append("    Review necessity of all components")
                details.append("    Monitor bundle performance during peak usage")
            
            # Determine overall status
            if depth_violations or component_violations or cycles:
                status = "failed"
                violations_msg = []
                if depth_violations:
                    violations_msg.append(f"{len(depth_violations)} depth violations")
                if component_violations:
                    violations_msg.append(f"{len(component_violations)} component violations")
                if cycles:
                    violations_msg.append(f"{len(cycles)} circular dependencies")
                message = f"Found {', '.join(violations_msg)}"
            elif warnings:
                status = "warning"
                message = f"Found {len(warnings)} bundles approaching component limits"
            else:
                status = "passed"
                message = "All bundles are within recommended depth and component limits with no circular dependencies"
            
            severity = "error" if status == "failed" else "warning" if status == "warning" else "info"
            
            self.add_result(
                "Bundle Analysis",
                status,
                message,
                details,
                severity
            )
            
        except Exception as e:
            self.add_result(
                "Bundle Analysis",
                "failed",
                f"Error analyzing bundle hierarchy: {str(e)}",
                severity="error"
            )
    
    def _process_attribute_override_check(self, bundle_products, parent_child_map):
        """Process attribute override check logic."""
        try:
            violated_bundles = []
            error_bundles = []
            details_list = []
            
            # Process bundles in parallel batches
            def process_bundle(bundle):
                bundle_id = bundle['Id']
                bundle_name = bundle['Name']
                
                try:
                    all_product_ids = self._get_all_products_in_bundle_optimized(bundle_id, parent_child_map)
                    
                    if not all_product_ids:
                        return bundle_name, 0, None
                    
                    id_list = "','".join(all_product_ids)
                    query = f"SELECT COUNT(Id) FROM ProductAttributeDefinition WHERE Product2Id IN ('{id_list}')"
                    
                    count_result = self.sf.query(query)
                    attribute_count = count_result['totalSize']
                    
                    violation = None
                    if attribute_count > 600:
                        violation = f"Bundle '{bundle_name}' has {attribute_count} attributes, which exceeds the limit of 600."
                    
                    return bundle_name, attribute_count, violation
                    
                except Exception as e:
                    return bundle_name, 0, f"Error processing bundle '{bundle_name}': {e}"
            
            # Process bundles in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_bundle = {executor.submit(process_bundle, bundle): bundle for bundle in bundle_products}
                
                for future in as_completed(future_to_bundle):
                    bundle_name, attribute_count, result = future.result()
                    
                    if isinstance(result, str) and result.startswith("Error"):
                        error_bundles.append(result)
                    else:
                        details_list.append(f"Bundle '{bundle_name}' has {attribute_count} attribute overrides.")
                        if result:  # violation
                            violated_bundles.append(result)
            
            # Determine overall status and message
            if violated_bundles or error_bundles:
                status = "failed"
                messages = []
                if violated_bundles:
                    messages.append(f"{len(violated_bundles)} bundle(s) exceeded the attribute limit")
                if error_bundles:
                    messages.append(f"encountered errors on {len(error_bundles)} bundle(s)")
                message = ", and ".join(messages) + "."
                severity = "error"
            else:
                status = "passed"
                message = "All bundles are within the recommended attribute override limits."
                severity = "info"
                
            # Construct details
            details = []
            if violated_bundles:
                details.append("Violations Found:")
                for violation in violated_bundles:
                    details.append(f"   • {violation}")
                details.append("🔧 Recommendations:")
                details.append("   • Review the bundle structure and attribute usage.")
                details.append("   • Consider reducing the number of attributes or splitting large bundles.")
            
            if error_bundles:
                details.append("Processing Errors:")
                for error in error_bundles:
                    details.append(f"   • {error}")
            
            details.append("Scan Details:")
            for detail in details_list:
                details.append(f"   • {detail}")
            
            self.add_result(
                "Attribute Override Check",
                status,
                message,
                details,
                severity
            )
            
        except Exception as e:
            self.add_result(
                "Attribute Override Check",
                "failed",
                f"Error in attribute override check: {str(e)}",
                severity="error"
            )
    
    def _get_all_products_in_bundle_optimized(self, product_id, parent_child_map, visited_products=None):
        """Optimized version using pre-fetched parent_child_map."""
        if visited_products is None:
            visited_products = set()
        
        if product_id in visited_products:
            return set()
        
        visited_products.add(product_id)
        all_ids = {product_id}
        
        # Use pre-fetched data instead of making API calls
        components = parent_child_map.get(product_id, [])
        
        for component in components:
            child_id = component['ChildProductId']
            if child_id:  # Additional safety check
                all_ids.update(self._get_all_products_in_bundle_optimized(child_id, parent_child_map, visited_products))
        
        return all_ids
    
    def _analyze_bundle_hierarchy(self, bundle_id, parent_child_map, current_depth=1, visited=None):
        """
        Recursively analyze bundle hierarchy to calculate depth and component count.
        
        Args:
            bundle_id: ID of the bundle to analyze
            parent_child_map: Dictionary mapping parent IDs to child components
            current_depth: Current depth in the hierarchy
            visited: Set of visited bundle IDs to prevent infinite loops
            
        Returns:
            tuple: (max_depth, total_components)
        """
        if visited is None:
            visited = set()
        
        # Prevent infinite loops
        if bundle_id in visited:
            return current_depth, 0
        
        visited.add(bundle_id)
        
        # Get components for this bundle
        components = parent_child_map.get(bundle_id, [])
        total_components = len(components)
        max_depth = current_depth
        
        # Analyze each child component
        for component in components:
            child_id = component['ChildProductId']
            child_type = component.get('ChildProduct', {}).get('Type', '')
            
            # If child is also a bundle, recursively analyze it
            if child_type == 'Bundle':
                child_depth, child_components = self._analyze_bundle_hierarchy(
                    child_id, parent_child_map, current_depth + 1, visited.copy()
                )
                max_depth = max(max_depth, child_depth)
                total_components += child_components
        
        return max_depth, total_components
    
    def _detect_bundle_cycles(self, bundle_products, parent_child_map):
        """Detect circular dependencies in bundle hierarchy using DFS."""
        # Create bundle name map for better reporting
        bundle_name_map = {bundle['Id']: bundle['Name'] for bundle in bundle_products}
        
        # Build bundle-only adjacency list (parent -> children that are bundles)
        bundle_graph = {}
        for bundle in bundle_products:
            bundle_id = bundle['Id']
            bundle_graph[bundle_id] = []
            
            # Get child components that are also bundles
            components = parent_child_map.get(bundle_id, [])
            for component in components:
                child_id = component['ChildProductId']
                child_type = component.get('ChildProduct', {}).get('Type', '')
                if child_type == 'Bundle':
                    bundle_graph[bundle_id].append(child_id)
        
        # DFS cycle detection with three colors
        WHITE = 0  # Unvisited
        GRAY = 1   # Currently being processed (in recursion stack)
        BLACK = 2  # Fully processed
        
        colors = {bundle_id: WHITE for bundle_id in bundle_graph}
        cycles = []
        
        def dfs(node, path):
            """DFS helper function to detect cycles."""
            if colors[node] == GRAY:
                # Found a back edge - cycle detected
                cycle_start_idx = path.index(node)
                cycle_nodes = path[cycle_start_idx:] + [node]
                
                # Convert to bundle names for reporting
                cycle_names = [bundle_name_map.get(node_id, node_id) for node_id in cycle_nodes]
                cycle_path = " → ".join(cycle_names)
                
                cycles.append({
                    'cycle_path': cycle_path,
                    'cycle_length': len(cycle_nodes) - 1,  # Subtract 1 since we repeat the first node
                    'cycle_nodes': cycle_nodes[:-1]  # Remove the repeated node
                })
                return
            
            if colors[node] == BLACK:
                # Already processed, skip
                return
            
            # Mark as currently being processed
            colors[node] = GRAY
            
            # Visit all children
            for child in bundle_graph.get(node, []):
                dfs(child, path + [node])
            
            # Mark as fully processed
            colors[node] = BLACK
        
        # Run DFS from all unvisited nodes
        for bundle_id in bundle_graph:
            if colors[bundle_id] == WHITE:
                dfs(bundle_id, [])
        
        # Remove duplicate cycles (cycles that are rotations of each other)
        unique_cycles = []
        seen_cycles = set()
        
        for cycle in cycles:
            # Create a normalized representation by finding the minimum rotation
            nodes = cycle['cycle_nodes']
            min_rotation = min(nodes[i:] + nodes[:i] for i in range(len(nodes)))
            cycle_key = tuple(min_rotation)
            
            if cycle_key not in seen_cycles:
                seen_cycles.add(cycle_key)
                unique_cycles.append(cycle)
        
        return unique_cycles
    
    def run_attribute_picklist_integrity_check(self):
        """Check for orphaned, empty, and single-value attribute picklists."""
        self.current_check += 1
        self.update_progress("Attribute Picklist Integrity", "in_progress")
        
        try:
            # Query all active AttributePicklist records
            picklist_query = """
                SELECT Id, Name, Description, Status, DataType, UnitOfMeasureId
                FROM AttributePicklist 
                WHERE Status = 'Active'
            """
            
            picklist_results = self.sf.query_all(picklist_query)
            
            if picklist_results['totalSize'] == 0:
                self.add_result(
                    "Attribute Picklist Integrity",
                    "info",
                    "No active AttributePicklist records found in the org",
                    severity="info"
                )
                return
            
            # Query all AttributeDefinition records that reference picklists
            definition_query = """
                SELECT Id, Name, Label, DataType, PicklistId, Code, IsActive
                FROM AttributeDefinition 
                WHERE PicklistId != NULL AND IsActive = true
            """
            
            definition_results = self.sf.query_all(definition_query)
            
            # Query all AttributePicklistValue records
            value_query = """
                SELECT Id, PicklistId, Abbreviation, Status, Code, IsDefault, 
                       Sequence, DisplayValue, Value, Name
                FROM AttributePicklistValue
                WHERE PicklistId != NULL
            """
            
            value_results = self.sf.query_all(value_query)
            
            # Process the data
            self._process_attribute_picklist_data(
                picklist_results['records'],
                definition_results['records'],
                value_results['records']
            )
            
        except Exception as e:
            self.add_result(
                "Attribute Picklist Integrity",
                "failed",
                f"Error checking attribute picklist integrity: {str(e)}",
                severity="error"
            )
        
        self.update_progress("Attribute Picklist Integrity", "completed")
    
    def _process_attribute_picklist_data(self, picklists, definitions, values):
        """Process attribute picklist data and identify issues."""
        # Create lookup maps
        picklist_map = {pl['Id']: pl for pl in picklists}
        definition_map = {}
        value_map = {}
        
        # Group definitions by PicklistId
        for definition in definitions:
            picklist_id = definition['PicklistId']
            if picklist_id not in definition_map:
                definition_map[picklist_id] = []
            definition_map[picklist_id].append(definition)
        
        # Group values by PicklistId
        for value in values:
            picklist_id = value['PicklistId']
            if picklist_id not in value_map:
                value_map[picklist_id] = []
            value_map[picklist_id].append(value)
        
        # Find issues
        orphaned_picklists = []
        empty_picklists = []
        single_value_picklists = []
        
        for picklist_id, picklist in picklist_map.items():
            picklist_name = picklist.get('Name', 'Unknown')
            
            # Check for orphaned picklists (not referenced by any AttributeDefinition)
            if picklist_id not in definition_map:
                orphaned_picklists.append({
                    'id': picklist_id,
                    'name': picklist_name
                })
                continue
            
            # Check for empty picklists (no AttributePicklistValue records)
            if picklist_id not in value_map:
                empty_picklists.append({
                    'id': picklist_id,
                    'name': picklist_name,
                    'definitions': definition_map[picklist_id]
                })
                continue
            
            # Check for single-value picklists
            if len(value_map[picklist_id]) == 1:
                single_value_picklists.append({
                    'id': picklist_id,
                    'name': picklist_name,
                    'definitions': definition_map[picklist_id],
                    'value': value_map[picklist_id][0]
                })
        
        # Generate detailed results
        details = []
        details.append(f"Analyzed {len(picklists)} active AttributePicklist records")
        
        # Section 1: Orphaned Picklists
        details.append("🔗 Orphaned AttributePicklist Records:")
        if orphaned_picklists:
            details.append(f"⚠️ {len(orphaned_picklists)} orphaned picklists found:")
            for picklist in orphaned_picklists:
                details.append(f"   • {picklist['name']} - Not referenced by any AttributeDefinition")
        else:
            details.append("✅ No orphaned picklists found")
        
        # Section 2: Empty Picklists
        details.append("📋 Empty AttributePicklist Records:")
        if empty_picklists:
            details.append(f"⚠️ {len(empty_picklists)} empty picklists found:")
            for picklist in empty_picklists:
                definition_names = [d['Name'] for d in picklist['definitions']]
                details.append(f"   • {picklist['name']} - No AttributePicklistValue records")
                details.append(f"     Used by AttributeDefinitions: {', '.join(definition_names)}")
        else:
            details.append("✅ No empty picklists found")
        
        # Section 3: Single-Value Picklists
        details.append("🔢 Single-Value AttributePicklist Records:")
        if single_value_picklists:
            details.append(f"💡 {len(single_value_picklists)} single-value picklists found:")
            for picklist in single_value_picklists:
                definition_names = [d['Name'] for d in picklist['definitions']]
                value_info = picklist['value']
                details.append(f"   • {picklist['name']} - Only one value: '{value_info.get('DisplayValue', value_info.get('Value', 'N/A'))}'")
                details.append(f"     Used by AttributeDefinitions: {', '.join(definition_names)}")
        else:
            details.append("✅ No single-value picklists found")
        
        # Add recommendations
        if orphaned_picklists or empty_picklists or single_value_picklists:
            details.append("🔧 Recommendations:")
            if orphaned_picklists:
                details.append("    • Remove orphaned AttributePicklist records to clean up data")
                details.append("    • Or create AttributeDefinition records that reference these picklists")
            if empty_picklists:
                details.append("    • Add AttributePicklistValue records to empty picklists")
                details.append("    • Or consider using Text datatype instead of picklist")
            if single_value_picklists:
                details.append("    • Consider changing AttributeDefinition datatype from 'Picklist' to 'Text' for single-value picklists")
                details.append("    • This simplifies data entry and reduces complexity")
                details.append("    • Or add more AttributePicklistValue records if multiple values are needed")
        
        # Determine overall status
        if orphaned_picklists or empty_picklists:
            status = "failed"
            issues = []
            if orphaned_picklists:
                issues.append(f"{len(orphaned_picklists)} orphaned picklists")
            if empty_picklists:
                issues.append(f"{len(empty_picklists)} empty picklists")
            if single_value_picklists:
                issues.append(f"{len(single_value_picklists)} single-value picklists")
            message = f"Found {', '.join(issues)}"
        elif single_value_picklists:
            status = "warning"
            message = f"Found {len(single_value_picklists)} single-value picklists that could be optimized"
        else:
            status = "passed"
            message = "All AttributePicklist records are properly configured and referenced"
        
        severity = "error" if status == "failed" else "warning" if status == "warning" else "info"
        
        self.add_result(
            "Attribute Picklist Integrity",
            status,
            message,
            details,
            severity
        )
    
    def run_all_checks(self):
        """Run all available health checks with optimized queries."""
        self.results = []  # Clear previous results
        self.current_check = 0
        
        self.update_progress("Starting Health Checks", "starting", 0)
        
        # Run individual checks
        self.run_basic_org_info_check()
        self.run_owd_sharing_check()
        self.run_optimized_bundle_checks()
        self.run_attribute_picklist_integrity_check()
        
        self.update_progress("Health Checks Complete", "completed", 100)
        
        # Calculate overall health score
        return self._calculate_health_score()
    
    def _calculate_health_score(self):
        """Calculate overall health score based on individual checks."""
        if not self.results:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {},
                "overall_health": {
                    "score": 0,
                    "grade": "F",
                    "summary": {
                        "total_checks": 0,
                        "ok": 0,
                        "warnings": 0,
                        "errors": 0
                    }
                }
            }
        
        # Convert results to the expected format
        checks = {}
        for result in self.results:
            # Map status to expected format
            status_map = {
                "passed": "ok",
                "warning": "warning", 
                "failed": "error",
                "info": "ok"
            }
            
            checks[result.check_name.lower().replace(" ", "_")] = {
                "status": status_map.get(result.status, "error"),
                "message": result.message,
                "details": {
                    "timestamp": result.timestamp.isoformat(),
                    "severity": result.severity,
                    "details": result.details
                }
            }
        
        # Calculate score
        total_checks = len(self.results)
        ok_count = sum(1 for result in self.results if result.status in ["passed", "info"])
        warning_count = sum(1 for result in self.results if result.status == "warning")
        error_count = sum(1 for result in self.results if result.status == "failed")
        
        # Calculate score (ok=1, warning=0.5, error=0)
        score = (ok_count + warning_count * 0.5) / total_checks * 100 if total_checks > 0 else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "overall_health": {
                "score": round(score, 2),
                "grade": self._get_health_grade(score),
                "summary": {
                    "total_checks": total_checks,
                    "ok": ok_count,
                    "warnings": warning_count,
                    "errors": error_count
                }
            }
        }

    def _get_health_grade(self, score):
        """Get health grade based on score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"