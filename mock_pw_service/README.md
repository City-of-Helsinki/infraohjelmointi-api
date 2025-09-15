# Mock ProjectWise Service

A comprehensive mock service that accurately simulates the ProjectWise API for testing and debugging the IO-396 sync functionality.

## 🎯 **What This Mock Service Provides**

### **Core PW Behavior Simulation**

- ✅ **Minimal payload enforcement** - Rejects updates with >8 fields (just like real PW)
- ✅ **Protected field logic** - Won't overwrite fields if PW has data
- ✅ **Hierarchical field handling** - One-at-a-time updates required
- ✅ **Accurate field mappings** - Uses real PW field names from refactoring

### **Enhanced Testing Capabilities**

- ✅ **Error simulation** - Configurable error rates and realistic error responses
- ✅ **Performance simulation** - Realistic network delays and timeouts
- ✅ **Enhanced logging** - Field-level change tracking and detailed operation logs
- ✅ **Performance metrics** - Track requests, errors, delays, and success rates

### **Easy Integration**

- ✅ **Environment variable switching** - Easy toggle between mock and real PW
- ✅ **Configurable behavior** - Adjust error rates, delays, and other parameters
- ✅ **Web UI dashboard** - Real-time monitoring and debugging interface

## Quick Start

```bash
# Build and run
docker-compose up --build

# Or run directly
docker build -t mock-pw .
docker run -p 8080:8080 -v $(pwd)/data:/data mock-pw
```

## Configuration

### **Environment Variables**

```bash
# Enable/disable mock mode (default: true)
PW_MOCK_MODE=true

# Error simulation rate (default: 0.1 = 10%)
PW_ERROR_RATE=0.1

# Maximum delay in seconds (default: 2.0)
PW_MAX_DELAY=2.0
```

### **Example Usage**

```bash
# Run with custom error rate and delay
PW_ERROR_RATE=0.2 PW_MAX_DELAY=5.0 python app.py

# Run with no errors (perfect conditions)
PW_ERROR_RATE=0.0 PW_MAX_DELAY=0.1 python app.py

# Run with high error rate (stress testing)
PW_ERROR_RATE=0.5 PW_MAX_DELAY=10.0 python app.py
```

## Usage

1. **Web UI**: http://localhost:8080

   - View all synced projects
   - Inspect field values
   - See sync operation log
   - Reset test data

2. **Configure Infrastructure Tool**:

   ```bash
   # Set these environment variables in your .env
   PW_API_URL=http://localhost:8080/pwapi/
   PW_API_PROJECT_META_ENDPOINT=iModelConnectedProjects/
   PW_PROJECT_UPDATE_ENDPOINT=iModelConnectedProjects/schemas/{schema}/classes/{class}/instances/
   ```

3. **Test Sync**:

   ```bash
   # Run test scope sync
   python manage.py projectimporter --sync-projects-to-pw-test-scope

   # Check results in web UI
   open http://localhost:8080
   ```

## API Endpoints

### **ProjectWise Compatible**

- `GET /pwapi/iModelConnectedProjects/{id}` - Get project metadata
- `POST /pwapi/iModelConnectedProjects/schemas/{schema}/classes/{class}/instances/{id}` - Update project

### **Management & Monitoring**

- `GET /` - Web UI dashboard
- `GET /api/status` - Service status and statistics
- `GET /api/performance` - Performance metrics and error rates
- `GET /api/sync-log` - Detailed sync operations log
- `POST /api/clear` - Reset all data (for testing)

### **Testing & Debugging**

- `GET /api/projects` - List all projects (JSON)
- `POST /api/test-scenarios` - Run predefined test scenarios
- `GET /api/field-mappings` - View field mapping configuration

## Features

- ✅ **Realistic PW field structure** - Uses actual PW field names
- ✅ **Issue reproduction** - Pre-populated with data that causes known issues
- ✅ **Visual feedback** - Web UI highlights problem fields
- ✅ **Persistent storage** - Data survives container restarts
- ✅ **Sync logging** - Detailed log of all operations
- ✅ **Auto-refresh** - UI updates automatically

## Testing the Issues

The mock service creates projects with realistic "problematic" data:

```json
{
  "PROJECT_Hankkeen_vaihe": "1. Hanke-ehdotus", // Issue 1: Should update to "2. Ohjelmointi"
  "PROJECT_Pluokka": "Existing Pääluokka", // Issue 2: Should update from infra tool
  "PROJECT_Louhi__hankkeen_valmistumisvuosi": 2026, // Issue 3a: Should update to 2027
  "PROJECT_Hankkeen_rakentaminen_pttyy": "31.12.2026", // Issue 3b: Does update correctly
  "PROJECT_Suurpiirin_nimi": "Existing Suurpiiri" // Issue 4: Should update
}
```

## Data Persistence

Project data is stored in `/data/pw_projects.json` and persists between container restarts.

## Development

```bash
# Run locally (without Docker)
pip install flask
python app.py

# Access at http://localhost:8080
```
