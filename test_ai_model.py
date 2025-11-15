#!/usr/bin/env python
"""
Test script to check the AI model's risk analysis capabilities.
Run this to see example logs being analyzed.
"""

from whitehat_app.ai_service import ai_service

# Example logs with different risk levels
example_logs = [
    {
        "name": "Normal Login",
        "data": {
            "action_type": "login",
            "resource_type": "authentication",
            "resource_accessed": "user_portal",
            "request_status": "success",
            "employee_id": "EMP001"
        }
    },
    {
        "name": "Suspicious Activity - Bulk Download",
        "data": {
            "action_type": "bulk_download",
            "resource_type": "file_system",
            "resource_accessed": "confidential_reports",
            "request_status": "success",
            "employee_id": "EMP002"
        }
    },
    {
        "name": "Critical Risk - Export Sensitive Data",
        "data": {
            "action_type": "export_sensitive_data",
            "resource_type": "database",
            "resource_accessed": "customer_records",
            "request_status": "success",
            "employee_id": "EMP003"
        }
    },
    {
        "name": "Failed Access to Restricted Resource",
        "data": {
            "action_type": "access_file",
            "resource_type": "file_system",
            "resource_accessed": "restricted_documents",
            "request_status": "failed",
            "employee_id": "EMP004"
        }
    },
    {
        "name": "Unusual Activity - Multiple Failed Logins",
        "data": {
            "action_type": "failed_authentication",
            "resource_type": "authentication",
            "resource_accessed": "admin_panel",
            "request_status": "failed",
            "employee_id": "EMP005"
        }
    },
    {
        "name": "Standard Document View",
        "data": {
            "action_type": "view_document",
            "resource_type": "file_system",
            "resource_accessed": "project_proposal.pdf",
            "request_status": "success",
            "employee_id": "EMP006"
        }
    }
]

def test_ai_model():
    """Test the AI model with example logs."""
    print("=" * 80)
    print("AI MODEL RISK ANALYSIS TEST")
    print("=" * 80)
    print()
    
    for example in example_logs:
        print(f"📋 Testing: {example['name']}")
        print("-" * 80)
        print("Log Details:")
        for key, value in example['data'].items():
            print(f"  • {key}: {value}")
        print()
        
        try:
            result = ai_service.analyze_log_risk(example['data'])
            
            print("✅ Analysis Result:")
            print(f"  • Risk Level: {result['risk_level']}")
            print(f"  • Create Incident: {result['create_incident']}")
            print(f"  • Description: {result['description']}")
            
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
        
        print()
        print()

if __name__ == "__main__":
    test_ai_model()
