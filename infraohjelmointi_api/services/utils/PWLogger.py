"""
ProjectWise logging utilities - centralized, maintainable logging for PW operations.
"""

import logging
import time
from typing import Dict, List, Optional, Any
from infraohjelmointi_api.services.utils.PWConfig import PWConfig

# Module-level logger
logger = logging.getLogger("infraohjelmointi_api")


class PWLogger:
    """Centralized logging utilities for ProjectWise operations."""
    
    @staticmethod
    def log_sync_start(project_name: str, hkr_id: str, sync_type: str = "AUTOMATIC SYNC") -> float:
        """
        Log the start of a sync operation and return start time for performance tracking.
        
        Args:
            project_name: Name of the project being synced
            hkr_id: HKR ID of the project
            sync_type: Type of sync (AUTOMATIC SYNC, MASS UPDATE, etc.)
            
        Returns:
            float: Start time for performance calculations
        """
        
        start_time = time.time()
        
        logger.info(f"\n{'='*PWConfig.LOG_SEPARATOR_LENGTH}")
        logger.info(f"{sync_type}: {project_name} (HKR ID: {hkr_id})")
        logger.info(f"{'='*PWConfig.LOG_SEPARATOR_LENGTH}")
        logger.debug(f"Sync started at: {time.strftime('%H:%M:%S')}")
        
        return start_time
    
    @staticmethod
    def log_data_preparation(project_name: str, pw_data: Dict[str, Any], 
                           filtered_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log data preparation details with field analysis.
        
        Args:
            project_name: Name of the project
            pw_data: PW-formatted data to be synced
            filtered_data: Original data before filtering (for comparison)
        """
        
        logger.info(f"Data prepared for PW sync: {len(pw_data)} fields")
        logger.debug(f"Fields to update: {list(pw_data.keys())}")
        logger.debug(f"Full PW data payload: {pw_data}")
        
        # Field-by-field analysis
        if pw_data:
            logger.info(f"Field analysis for '{project_name}':")
            for field, value in pw_data.items():
                logger.debug(f"  {field}: {value}")
            logger.info(f"Total fields to sync: {len(pw_data)}")
    
    @staticmethod
    def log_overwrite_rules(project_name: str, filtered_out: Dict[str, Any]) -> None:
        """
        Log overwrite rules filtering results.
        
        Args:
            project_name: Name of the project
            filtered_out: Fields that were filtered out by overwrite rules
        """
        
        if filtered_out:
            logger.debug(f"Fields filtered out by overwrite rules for '{project_name}': {list(filtered_out.keys())}")
            
            field_categories = {
                'classification': [f for f in filtered_out.keys() if f in PWConfig.CLASSIFICATION_FIELDS],
                'protected': [f for f in filtered_out.keys() if f in PWConfig.PROTECTED_FIELDS],
                'empty_tool': [f for f in filtered_out.keys() if f not in PWConfig.CLASSIFICATION_FIELDS and f not in PWConfig.PROTECTED_FIELDS]
            }
            
            for category, fields in field_categories.items():
                if fields:
                    logger.info(f"  Filtered ({category}): {fields}")
    
    @staticmethod
    def log_update_operation(project_name: str, hkr_id: str, pw_instance_id: str, 
                           normal_fields: Dict[str, Any], hierarchical_fields: Dict[str, Any]) -> None:
        """
        Log the actual update operation details.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            pw_instance_id: PW instance ID
            normal_fields: Normal fields to update
            hierarchical_fields: Hierarchical fields to update
        """
        
        logger.info(f"=" * PWConfig.LOG_SEPARATOR_LENGTH)
        logger.info(f"UPDATING PROJECT: '{project_name}' (HKR ID: {hkr_id})")
        logger.info(f"PW Instance ID: {pw_instance_id}")
        
        # Log normal fields update
        if normal_fields:
            logger.info(f"Updating {len(normal_fields)} normal fields in batch")
            logger.debug(f"Normal fields: {list(normal_fields.keys())}")
            logger.info(f"Normal fields update: {list(normal_fields.keys())}")
        
        # Log hierarchical fields update
        if hierarchical_fields:
            logger.info(f"Updating {len(hierarchical_fields)} hierarchical fields individually")
            logger.debug(f"Hierarchical fields: {list(hierarchical_fields.keys())}")
    
    @staticmethod
    def log_field_update_result(success: bool, field_type: str, field_count: int) -> None:
        """
        Log the result of a field update operation.
        
        Args:
            success: Whether the update was successful
            field_type: Type of fields (normal, hierarchical)
            field_count: Number of fields updated
        """
        
        status = "[OK]" if success else "[FAIL]"
        logger.info(f"{status} {field_type} fields updated successfully" if success else f"{status} {field_type} fields update failed")
    
    @staticmethod
    def log_sync_result(project_name: str, hkr_id: str, total_attempted: int, total_succeeded: int,
                       normal_attempted: int, hierarchical_attempted: int, start_time: float) -> None:
        """
        Log the final sync result with performance metrics.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            total_attempted: Total fields attempted
            total_succeeded: Total fields succeeded
            normal_attempted: Normal fields attempted
            hierarchical_attempted: Hierarchical fields attempted
            start_time: Start time from log_sync_start
        """
        
        # Calculate performance metrics
        sync_duration = time.time() - start_time
        fields_per_second = total_succeeded / sync_duration if sync_duration > 0 else 0
        
        logger.info(f"=" * PWConfig.LOG_SEPARATOR_LENGTH)
        logger.info(f"AUTOMATIC SYNC RESULT: {total_succeeded}/{total_attempted} fields updated")
        logger.info(f"Project: '{project_name}' (HKR ID: {hkr_id})")
        logger.info(f"Normal fields: {normal_attempted} attempted")
        logger.info(f"Hierarchical fields: {hierarchical_attempted} attempted")
        logger.info(f"Performance: {sync_duration:.2f}s total, {fields_per_second:.1f} fields/sec")
        logger.info(f"Sync completed at: {time.strftime('%H:%M:%S')}")
        logger.info(f"=" * PWConfig.LOG_SEPARATOR_LENGTH)
    
    @staticmethod
    def log_sync_error(project_name: str, hkr_id: str, error: Exception, 
                      data_attempted: Optional[Dict[str, Any]] = None) -> None:
        """
        Log sync error with comprehensive context.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            error: The exception that occurred
            data_attempted: Data that was being synced when error occurred
        """
        
        logger.error(f"=" * PWConfig.LOG_SEPARATOR_LENGTH)
        logger.error(f"AUTOMATIC SYNC FAILED: {project_name} (HKR ID: {hkr_id})")
        logger.error(f"Error type: {type(error).__name__}")
        logger.error(f"Error message: {str(error)}")
        logger.error(f"Project data attempted: {len(data_attempted) if data_attempted else 0} fields")
        logger.error(f"Time: {time.strftime('%H:%M:%S')}")
        logger.error(f"=" * PWConfig.LOG_SEPARATOR_LENGTH)
    
    @staticmethod
    def log_mass_update_progress(project_name: str, hkr_id: str, current: int, total: int) -> None:
        """
        Log mass update progress for a single project.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            current: Current project number
            total: Total projects
        """
        
        logger.info(f"\n{'='*PWConfig.LOG_SEPARATOR_LENGTH}")
        logger.info(f"PROCESSING PROJECT {current}/{total}: {project_name} (HKR ID: {hkr_id})")
        logger.info(f"{'='*PWConfig.LOG_SEPARATOR_LENGTH}")
    
    @staticmethod
    def log_mass_update_summary(successful: int, skipped: int, errors: int) -> None:
        """
        Log mass update final summary.
        
        Args:
            successful: Number of successful updates
            skipped: Number of skipped updates
            errors: Number of errors
        """
        
        logger.info(f"Mass update completed (all programmed projects): {successful} successful, {skipped} skipped, {errors} errors")
        
        if errors > 0:
            logger.warning(f"{errors} projects failed to update - check logs for details")
    
    @staticmethod
    def log_hierarchical_field_update_start(project_name: str, hkr_id: str, total_count: int) -> None:
        """
        Log the start of hierarchical field updates.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            total_count: Total number of hierarchical fields to update
        """
        
        logger.info(f"Updating {total_count} hierarchical fields one-at-a-time for '{project_name}' (HKR {hkr_id})")
    
    @staticmethod
    def log_hierarchical_field_result(field_name: str, field_value: str, success: bool, 
                                    status_code: Optional[int] = None, error_message: Optional[str] = None) -> None:
        """
        Log the result of a single hierarchical field update.
        
        Args:
            field_name: Name of the field being updated
            field_value: Value being set
            success: Whether the update was successful
            status_code: HTTP status code (if available)
            error_message: Error message (if available)
        """
        
        if success:
            logger.info(f"  [OK] {field_name}: '{field_value}' - SUCCESS")
        else:
            if status_code:
                logger.warning(f"  [FAIL] {field_name}: '{field_value}' - FAILED (status {status_code})")
                if error_message:
                    logger.warning(f"    Error: {error_message}")
            else:
                logger.error(f"  [ERROR] {field_name}: Exception - {field_value}")
    
    @staticmethod
    def log_api_request(api_url: str, operation: str = "API") -> None:
        """
        Log API request details.
        
        Args:
            api_url: The API URL being requested
            operation: Description of the operation
        """
        
        logger.debug(f"Requesting {operation} {api_url}")
    
    @staticmethod
    def log_api_response(response_time: float, result_count: Optional[int] = None, 
                        operation: str = "API") -> None:
        """
        Log API response details.
        
        Args:
            response_time: Time taken for the response
            result_count: Number of results returned (if applicable)
            operation: Description of the operation
        """
        
        if result_count is not None:
            logger.info(f"{operation} responded with {result_count} results")
        logger.debug(f"{operation} responded in {response_time:.3f}s")
    
    @staticmethod
    def log_data_processing(project_name: str, data_type: str, field_count: int, 
                          details: Optional[str] = None) -> None:
        """
        Log data processing details.
        
        Args:
            project_name: Name of the project
            data_type: Type of data being processed
            field_count: Number of fields processed
            details: Additional details about the processing
        """
        
        base_message = f"{data_type} for {project_name} with {field_count} fields"
        if details:
            logger.debug(f"{base_message}: {details}")
        else:
            logger.debug(f"{base_message}")
    
    @staticmethod
    def log_field_processing_error(field_name: str, error: Exception, action: str = "processing") -> None:
        """
        Log field processing errors.
        
        Args:
            field_name: Name of the field causing the error
            error: The exception that occurred
            action: Action being performed when error occurred
        """
        
        logger.error(f"Error {action} field '{field_name}': {str(error)}")
        logger.warning(f"SKIP: Field '{field_name}' - validation failed, not sending to PW")
    
    @staticmethod
    def log_no_data_to_sync(project_name: str, hkr_id: str, reason: str = "all fields are None") -> None:
        """
        Log when there's no data to sync for a project.
        
        Args:
            project_name: Name of the project
            hkr_id: HKR ID of the project
            reason: Reason why there's no data to sync
        """
        
        logger.info(f"No data to sync for project '{project_name}' (HKR ID: {hkr_id}) - {reason}")
    
    @staticmethod
    def log_sync_disabled_warning() -> None:
        """
        Log warning when sync is disabled.
        """
        
        logger.warning(
            "ProjectWise sync is DISABLED (PW_SYNC_ENABLED=False). "
            "Skipping sync to prevent dev/local data from reaching production PW. "
            "Set PW_SYNC_ENABLED=True in production environment only."
        )
    
    @staticmethod
    def log_mass_update_start(total_projects: int) -> None:
        """
        Log the start of mass update operation.
        
        Args:
            total_projects: Total number of projects to process
        """
        
        logger.info(f"Starting mass update of {total_projects} all programmed projects to PW")
    
    @staticmethod
    def log_mass_update_no_projects() -> None:
        """
        Log when no projects are found for mass update.
        """
        
        logger.warning(f"No projects found for mass update (all programmed projects)")
    
    @staticmethod
    def log_project_processing_error(project_name: str, error: Exception) -> None:
        """
        Log when a project fails to process during mass update.
        
        Args:
            project_name: Name of the project that failed
            error: The exception that occurred
        """
        
        logger.error(f"Failed to update project {project_name}: {str(error)}")
    
    @staticmethod
    def log_field_decision(field_name: str, decision: str, reason: str, 
                          data_value: str = None, pw_value: str = None) -> None:
        """
        Log field processing decisions for debugging.
        
        Args:
            field_name: Name of the field
            decision: Decision made (SKIP, INCLUDE, etc.)
            reason: Reason for the decision
            data_value: Value from infra tool (optional)
            pw_value: Value from PW (optional)
        """
        
        if decision == "SKIP":
            if data_value and pw_value:
                logger.debug(f"SKIP: {reason} '{field_name}' - PW has data: '{pw_value}'")
            else:
                logger.debug(f"SKIP: {reason} '{field_name}' - {reason}")
        elif decision == "INCLUDE":
            if data_value:
                logger.debug(f"INCLUDE: {reason} '{field_name}' - infra tool has data (value: {data_value})")
            else:
                logger.debug(f"INCLUDE: {reason} '{field_name}' - {reason}")
        else:
            logger.debug(f"{decision}: {reason} '{field_name}'")
