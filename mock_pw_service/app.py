#!/usr/bin/env python3
"""
Enhanced Mock ProjectWise API Service for IO-396 Testing

This service provides a complete mock PW environment with:
- Working API endpoints that match the real PW API
- Web UI for inspecting synced data and logs
- Persistent storage of project data
- Support for dynamic HKR ID handling
- Real-time sync operation logging

Usage:
    docker run -p 8080:8080 mock-pw-service
    
Web UI: http://localhost:8080
API Base: http://localhost:8080/pwapi/
"""

from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import json
import os
import re
from typing import Dict, Any, List

app = Flask(__name__)

# ============================================================================
# ENVIRONMENT CONFIGURATION (Step 3 - Integration)
# ============================================================================

# Environment variable support for easy switching between mock and real PW
MOCK_MODE = os.getenv('PW_MOCK_MODE', 'true').lower() == 'true'
ERROR_RATE = float(os.getenv('PW_ERROR_RATE', '0.1'))  # 10% default error rate
MAX_DELAY = float(os.getenv('PW_MAX_DELAY', '2.0'))    # 2s max delay

print(f"🔧 Mock PW Service Configuration:")
print(f"   MOCK_MODE: {MOCK_MODE}")
print(f"   ERROR_RATE: {ERROR_RATE:.1%}")
print(f"   MAX_DELAY: {MAX_DELAY}s")

# ============================================================================
# FIELD MAPPINGS (Step 1 - Accurate field names from refactoring)
# ============================================================================

FIELD_MAPPINGS = {
    'name': 'PROJECT_Kohde',
    'description': 'PROJECT_Hankkeen_kuvaus',
    'phase': 'PROJECT_Hankkeen_vaihe',
    'projectClass': 'PROJECT_Pluokka',
    'projectDistrict': 'PROJECT_Suurpiirin_nimi',
    'programmed': 'PROJECT_Ohjelmoitu',
    'planningStartYear': 'PROJECT_Louhi__hankkeen_aloitusvuosi',
    'constructionEndYear': 'PROJECT_Louhi__hankkeen_valmistumisvuosi',
    'gravel': 'PROJECT_Sorakatu',
    'louhi': 'PROJECT_Louheen',
    'address': 'PROJECT_Kadun_tai_puiston_nimi',
    'area': 'PROJECT_Projektialue',
    'responsibleZone': 'PROJECT_Alue_rakennusviraston_vastuujaon_mukaan',
    'constructionPhaseDetail': 'PROJECT_Rakentamisvaiheen_tarkenne',
    'type': 'PROJECT_Toimiala',
    'personPlanning': 'PROJECT_Hankkeen_suunnittelu_alkaa',
    'personConstruction': 'PROJECT_Hankkeen_rakentaminen_alkaa',
    'estPlanningStart': 'PROJECT_Hankkeen_suunnittelu_alkaa',
    'estPlanningEnd': 'PROJECT_Hankkeen_suunnittelu_pttyy',
    'estConstructionStart': 'PROJECT_Hankkeen_rakentaminen_alkaa',
    'estConstructionEnd': 'PROJECT_Hankkeen_rakentaminen_pttyy',
    'presenceStart': 'PROJECT_Esillaolo_alku',
    'presenceEnd': 'PROJECT_Esillaolo_loppu',
    'visibilityStart': 'PROJECT_Nhtvillolo_alku',
    'visibilityEnd': 'PROJECT_Nhtvillolo_loppu',
    'masterPlanAreaNumber': 'PROJECT_Aluekokonaisuuden_nimi',
    'trafficPlanNumber': 'PROJECT_Liikennesuunnitelman_numero',
    'bridgeNumber': 'PROJECT_Sillan_numero'
}

# Storage configuration
STORAGE_FILE = '/data/mock_pw_data.json'
projects_data: Dict[str, Dict[str, Any]] = {}
sync_log: List[Dict[str, Any]] = []

# Performance metrics (Step 2)
performance_metrics = {
    'total_requests': 0,
    'total_errors': 0,
    'total_delay_time': 0.0,
    'last_24h_operations': 0
}

def load_data():
    """Load existing data from persistent storage"""
    global projects_data, sync_log
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                projects_data = data.get('projects', {})
                sync_log = data.get('sync_log', [])
            print(f"✅ Loaded {len(projects_data)} projects from storage")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            projects_data = {}
            sync_log = []
    else:
        print("📁 No existing data file found, starting fresh")

def save_data():
    """Save current data to persistent storage"""
    try:
        os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)
        with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'projects': projects_data,
                'sync_log': sync_log,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error saving data: {e}")

def log_sync_operation(operation: str, hkr_id: str, details: Dict[str, Any]):
    """Log a sync operation for debugging and UI display"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'operation': operation,
        'hkr_id': hkr_id,
        'details': details
    }
    sync_log.append(log_entry)
    
    # Keep only last 100 log entries
    if len(sync_log) > 100:
        sync_log.pop(0)
    
    save_data()
    print(f"📝 {operation}: HKR {hkr_id} - {details}")

def create_default_project(hkr_id: str) -> Dict[str, Any]:
    """Create a default project structure for the given HKR ID"""
    return {
        "instanceId": f"instance-{hkr_id}",
        "className": "Project", 
        "schemaName": "PW_WSG",
        "relationshipInstances": [{
            "relatedInstance": {
                "instanceId": f"instance-{hkr_id}",
                "properties": {
                    "PROJECT_HKRHanketunnus": hkr_id,
                    "PROJECT_Kohde": f"Project {hkr_id}",
                    "PROJECT_Hankkeen_kuvaus": "Will be updated by sync",
                    "PROJECT_Hankkeen_vaihe": "1. hanke-ehdotus",
                    "PROJECT_Pluokka": "Original Class",
                    "PROJECT_Luokka": "Original Subclass", 
                    "PROJECT_Alaluokka": "Original Sub-subclass",
                    "PROJECT_Suurpiirin_nimi": "Original District",
                    "PROJECT_Kaupunginosan_nimi": "Original Area",
                    "PROJECT_Louhi__hankkeen_aloitusvuosi": "2025",
                    "PROJECT_Louhi__hankkeen_valmistumisvuosi": "2026",
                    "PROJECT_Ohjelmoitu": "Ei",
                    "PROJECT_Sorakatu": "Ei",
                    "PROJECT_Louheen": "Ei"
                }
            }
        }]
    }

# ============================================================================
# Web UI Routes
# ============================================================================

@app.route('/')
def home():
    """Main dashboard showing synced projects and recent operations"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock ProjectWise Service - IO-396 Testing</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; padding: 20px; background: #f5f5f5; color: #333;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .header h1 { margin: 0; font-size: 2.2em; font-weight: 300; }
            .header p { margin: 10px 0 0; opacity: 0.9; font-size: 1.1em; }
            .stats { 
                display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px; margin-bottom: 30px;
            }
            .stat-card {
                background: white; padding: 25px; border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08); text-align: center;
            }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #667eea; margin-bottom: 5px; }
            .stat-label { color: #666; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; }
            .section { 
                background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            }
            .section h2 { 
                margin: 0 0 20px; color: #333; font-size: 1.5em; font-weight: 600;
                border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;
            }
            .project-grid {
                display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }
            .project-card {
                border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px;
                background: #fafafa; transition: all 0.2s ease;
            }
            .project-card:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .project-header { 
                font-weight: bold; color: #667eea; font-size: 1.1em; margin-bottom: 15px;
                border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;
            }
            .project-details { display: grid; gap: 8px; }
            .detail-row { display: grid; grid-template-columns: 140px 1fr; gap: 10px; font-size: 0.9em; }
            .detail-label { font-weight: 500; color: #666; }
            .detail-value { color: #333; word-break: break-word; }
            .log-container { max-height: 400px; overflow-y: auto; }
            .log-entry {
                padding: 15px; border-left: 4px solid #667eea; margin-bottom: 15px;
                background: #f8f9ff; border-radius: 0 8px 8px 0;
            }
            .log-header { 
                display: flex; justify-content: space-between; align-items: center;
                margin-bottom: 8px; font-weight: 600;
            }
            .log-time { color: #666; font-size: 0.9em; font-weight: normal; }
            .log-details { 
                background: white; padding: 10px; border-radius: 4px; font-family: monospace;
                font-size: 0.85em; color: #555; white-space: pre-wrap;
            }
            .no-data { 
                text-align: center; color: #666; font-style: italic; padding: 40px;
                background: #f8f9fa; border-radius: 8px;
            }
            .refresh-btn {
                background: #667eea; color: white; border: none; padding: 10px 20px;
                border-radius: 6px; cursor: pointer; font-size: 0.9em; margin-bottom: 20px;
            }
            .refresh-btn:hover { background: #5a6fd8; }
            .api-info {
                background: #e8f4fd; border: 1px solid #bee5eb; border-radius: 8px;
                padding: 20px; margin-bottom: 30px;
            }
            .api-info h3 { margin: 0 0 15px; color: #0c5460; }
            .endpoint { 
                background: white; padding: 8px 12px; border-radius: 4px; margin: 5px 0;
                font-family: monospace; font-size: 0.9em; border: 1px solid #dee2e6;
            }
        </style>
        <script>
            function refreshPage() { window.location.reload(); }
            function autoRefresh() { 
                setInterval(refreshPage, 30000); // Auto-refresh every 30 seconds
            }
            window.onload = autoRefresh;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 Mock ProjectWise Service</h1>
                <p>IO-396 Testing Environment • Active since {{ startup_time }}</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ project_count }}</div>
                    <div class="stat-label">Projects Stored</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ sync_count }}</div>
                    <div class="stat-label">Sync Operations</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ last_sync_time }}</div>
                    <div class="stat-label">Last Activity</div>
                </div>
            </div>

            <div class="api-info">
                <h3>🔌 API Endpoints Active</h3>
                <div class="endpoint">GET  /pwapi/PW_WSG/Project - Project metadata queries</div>
                <div class="endpoint">POST /pwapi/PW_WSG_Dynamic/PrType_1121_HKR_Hankerek_Hanke/{id} - Project updates</div>
            </div>

            <div class="section">
                <h2>📊 Synced Projects</h2>
                <button class="refresh-btn" onclick="refreshPage()">🔄 Refresh Data</button>
                
                {% if projects_data %}
                <div class="project-grid">
                    {% for hkr_id, project in projects_data.items() %}
                    <div class="project-card">
                        <div class="project-header">HKR ID: {{ hkr_id }}</div>
                        <div class="project-details">
                            {% set props = project.relationshipInstances[0].relatedInstance.properties %}
                            <div class="detail-row">
                                <span class="detail-label">Project Name:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Kohde', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Phase:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Hankkeen_vaihe', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Class:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Pluokka', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">District:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Suurpiirin_nimi', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Programmed:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Ohjelmoitu', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Planning Year:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Louhi__hankkeen_aloitusvuosi', 'N/A') }}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Construction Year:</span>
                                <span class="detail-value">{{ props.get('PROJECT_Louhi__hankkeen_valmistumisvuosi', 'N/A') }}</span>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="no-data">
                    <p>No projects synced yet. Start by running the sync command:</p>
                    <code>python manage.py projectimporter --sync-projects-to-pw-test-scope</code>
                </div>
                {% endif %}
            </div>

            <div class="section">
                <h2>📝 Recent Sync Operations</h2>
                
                {% if sync_log %}
                <div class="log-container">
                    {% for log in sync_log[:10] %}
                    <div class="log-entry">
                        <div class="log-header">
                            <span>{{ log.operation }} - HKR {{ log.hkr_id }}</span>
                            <span class="log-time">{{ log.timestamp }}</span>
                        </div>
                        <div class="log-details">{{ log.details | tojson(indent=2) }}</div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="no-data">
                    No sync operations logged yet. Sync operations will appear here in real-time.
                </div>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """
    
    startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_sync = sync_log[-1]['timestamp'] if sync_log else "Never"
    if last_sync != "Never":
        last_sync = datetime.fromisoformat(last_sync.replace('Z', '+00:00')).strftime("%H:%M:%S")
    
    return render_template_string(html_template,
        startup_time=startup_time,
        project_count=len(projects_data),
        sync_count=len(sync_log),
        last_sync_time=last_sync,
        projects_data=projects_data,
        sync_log=list(reversed(sync_log))  # Most recent first, converted to list
    )

# ============================================================================
# ProjectWise API Routes
# ============================================================================

@app.route('/pwapi/PW_WSG/Project', methods=['GET'])
def get_project():
    """Handle ProjectWise project metadata queries with dynamic HKR ID support"""
    filter_param = request.args.get('$filter', '')
    print(f"📥 GET Project request: {request.args}")
    print(f"📥 Filter parameter: '{filter_param}'")
    
    # Extract HKR ID from filter parameter - try multiple patterns
    hkr_id = None
    patterns = [
        r'PROJECT_HKRHanketunnus\+eq\+(\d+)',
        r'PROJECT_HKRHanketunnus eq (\d+)', 
        r'HKRHanketunnus\+eq\+(\d+)',
        r'HKRHanketunnus eq (\d+)'
    ]
    
    for pattern in patterns:
        hkr_match = re.search(pattern, filter_param)
        if hkr_match:
            hkr_id = hkr_match.group(1)
            break
    
    if hkr_id:
        print(f"🔍 Looking for HKR ID: {hkr_id}")
        
        # Get or create project for this HKR ID
        if hkr_id not in projects_data:
            print(f"➕ Creating new project for HKR {hkr_id}")
            projects_data[hkr_id] = create_default_project(hkr_id)
            log_sync_operation("PROJECT_CREATED", hkr_id, {"reason": "Auto-created for GET request"})
            save_data()
        
        project = projects_data[hkr_id]
        log_sync_operation("PROJECT_QUERY", hkr_id, {"filter": filter_param})
        
        print(f"✅ Returning project for HKR {hkr_id}")
        return jsonify({"instances": [project]})
    
    # No HKR ID found - still create a default project for testing
    print("⚠️  No HKR ID found in filter, creating default project")
    default_hkr = "2054"  # Default for testing
    if default_hkr not in projects_data:
        projects_data[default_hkr] = create_default_project(default_hkr)
        log_sync_operation("PROJECT_CREATED", default_hkr, {"reason": "Auto-created as fallback"})
        save_data()
    
    return jsonify({"instances": [projects_data[default_hkr]]})

@app.route('/pwapi/PW_WSG_Dynamic/PrType_1121_HKR_Hankerek_Hanke/<instance_id>', methods=['POST'])
def update_project(instance_id):
    """Handle ProjectWise project updates with comprehensive logging"""
    data = request.get_json()
    print(f"📤 POST Update request for instance: {instance_id}")
    print(f"📦 Update data received: {json.dumps(data, indent=2)}")
    
    if not data or 'instance' not in data:
        return jsonify({"error": "Invalid request data"}), 400
    
    instance_data = data['instance']
    properties = instance_data.get('properties', {})
    
    # Extract HKR ID from instance_id (format: instance-{hkr_id})
    hkr_id = instance_id.replace('instance-', '')
    
    # Get or create project
    if hkr_id not in projects_data:
        projects_data[hkr_id] = create_default_project(hkr_id)
        log_sync_operation("PROJECT_CREATED", hkr_id, {"reason": "Auto-created for POST update"})
    
    # Update project properties
    project = projects_data[hkr_id]
    current_props = project['relationshipInstances'][0]['relatedInstance']['properties']
    
    # ============================================================================
    # CORE PW BEHAVIOR SIMULATION (Step 1)
    # ============================================================================
    
    # 1. Minimal Payload Enforcement - PW rejects updates with too many fields
    if len(properties) > 8:  # PW rejects large payloads
        print(f"❌ PW rejects updates with too many properties: {len(properties)} > 8")
        return jsonify({
            "error": "PW rejects updates with too many properties",
            "message": "Send only changed fields (max 8 at once)",
            "received_fields": len(properties),
            "max_allowed": 8
        }), 400
    
    # 2. Protected Field Logic - Don't overwrite if PW has data
    protected_fields = [
        'PROJECT_Hankkeen_kuvaus', 'PROJECT_Esillaolo_alku',
        'PROJECT_Esillaolo_loppu', 'PROJECT_Nhtvillolo_alku',
        'PROJECT_Nhtvillolo_loppu'
    ]
    
    protected_fields_filtered = []
    for field in protected_fields:
        if field in properties and current_props.get(field) and current_props[field] != "":
            # PW has data, don't overwrite
            protected_fields_filtered.append(field)
            del properties[field]
            print(f"🛡️  Protected field '{field}' not overwritten (PW has data)")
    
    # 3. Hierarchical Field Simulation - One-at-a-time requirement
    hierarchical_fields = [
        'PROJECT_Pluokka', 'PROJECT_Luokka', 'PROJECT_Alaluokka',
        'PROJECT_Suurpiirin_nimi', 'PROJECT_Kaupunginosan_nimi',
        'PROJECT_Osa_alue'
    ]
    
    hierarchical_in_request = [f for f in properties.keys() if f in hierarchical_fields]
    if len(hierarchical_in_request) > 1:
        print(f"❌ Hierarchical fields must be updated one at a time: {hierarchical_in_request}")
        return jsonify({
            "error": "Hierarchical fields must be updated one at a time",
            "message": "Send only one hierarchical field per request",
            "hierarchical_fields_found": hierarchical_in_request
        }), 400
    
    # ============================================================================
    # ENHANCED TESTING CAPABILITIES (Step 2)
    # ============================================================================
    
    # 1. Error Simulation - Simulate random PW errors for testing
    import random
    ERROR_SCENARIOS = {
        'timeout': {'error': 'Request timeout', 'status': 408},
        'unauthorized': {'error': 'Unauthorized', 'status': 401},
        'not_found': {'error': 'Project not found', 'status': 404},
        'validation_error': {'error': 'Validation failed', 'status': 400},
        'service_unavailable': {'error': 'PW service temporarily unavailable', 'status': 503}
    }
    
    # Update performance metrics
    performance_metrics['total_requests'] += 1
    
    # Simulate random errors (configurable rate)
    if random.random() < ERROR_RATE:
        error_type = random.choice(list(ERROR_SCENARIOS.keys()))
        error_data = ERROR_SCENARIOS[error_type]
        performance_metrics['total_errors'] += 1
        print(f"🎲 Simulating PW error: {error_type}")
        return jsonify(error_data), error_data['status']
    
    # 2. Performance Simulation - Add realistic delays (configurable)
    import time
    delay = random.uniform(0.1, MAX_DELAY)  # Configurable delay range
    time.sleep(delay)
    performance_metrics['total_delay_time'] += delay
    print(f"⏱️  Simulated network delay: {delay:.2f}s")
    
    # 3. Enhanced Logging - Log PW behavior simulation
    if protected_fields_filtered or hierarchical_in_request:
        log_sync_operation("PW_BEHAVIOR_SIMULATION", hkr_id, {
            "protected_fields_filtered": protected_fields_filtered,
            "hierarchical_fields": hierarchical_in_request,
            "final_properties_count": len(properties),
            "simulated_delay": delay
        })
    
    # Track what changed with enhanced logging
    changes = {}
    for key, new_value in properties.items():
        old_value = current_props.get(key)
        if old_value != new_value:
            changes[key] = {"from": old_value, "to": new_value}
            current_props[key] = new_value
            
            # Enhanced field change logging
            log_sync_operation("FIELD_UPDATE", hkr_id, {
                "field": key,
                "old_value": old_value,
                "new_value": new_value,
                "change_type": "update" if old_value else "create"
            })
    
    # Update the project data
    projects_data[hkr_id] = project
    
    # Log the update operation
    log_sync_operation("PROJECT_UPDATED", hkr_id, {
        "instance_id": instance_id,
        "changes_count": len(changes),
        "changes": changes,
        "all_properties": properties
    })
    
    save_data()
    
    # Return success response
    response = {
        "message": f"Project {instance_id} updated successfully",
        "status": "success",
        "updated_properties": properties
    }
    
    print(f"✅ Project {hkr_id} updated with {len(changes)} changes")
    return jsonify(response)

# ============================================================================
# Utility Routes
# ============================================================================

@app.route('/api/status')
def api_status():
    """API status and statistics endpoint"""
    return jsonify({
        "status": "running",
        "projects_count": len(projects_data),
        "sync_operations": len(sync_log),
        "last_activity": sync_log[-1]['timestamp'] if sync_log else None,
        "uptime": datetime.now().isoformat(),
        "performance_metrics": performance_metrics
    })

@app.route('/api/performance')
def api_performance():
    """Performance metrics endpoint (Step 2)"""
    avg_delay = performance_metrics['total_delay_time'] / performance_metrics['total_requests'] if performance_metrics['total_requests'] > 0 else 0
    error_rate = performance_metrics['total_errors'] / performance_metrics['total_requests'] if performance_metrics['total_requests'] > 0 else 0
    
    return jsonify({
        "total_requests": performance_metrics['total_requests'],
        "total_errors": performance_metrics['total_errors'],
        "error_rate": f"{error_rate:.2%}",
        "average_delay": f"{avg_delay:.2f}s",
        "total_delay_time": f"{performance_metrics['total_delay_time']:.2f}s"
    })

@app.route('/api/clear', methods=['POST'])
def clear_data():
    """Clear all stored data (for testing)"""
    global projects_data, sync_log
    projects_data = {}
    sync_log = []
    save_data()
    return jsonify({"message": "All data cleared successfully"})

# ============================================================================
# Application Startup
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Enhanced Mock ProjectWise Service for IO-396")
    print("📁 Loading existing data...")
    load_data()
    print("🌐 Starting web server...")
    print("📊 Web UI will be available at: http://localhost:8080")
    print("🔌 API endpoints ready at: http://localhost:8080/pwapi/")
    
    app.run(host='0.0.0.0', port=8080, debug=True)