# Mock ProjectWise Service

A lightweight Docker-based mock service that mimics the ProjectWise API for testing the IO-396 sync functionality.

## 🚨 Critical Issues This Helps Test

Based on analysis of Petri's feedback, this mock service helps identify and test:

1. **Issue 1: Phase not updating** - Projects with "programming" phase don't update PW's "1. Hanke-ehdotus"
2. **Issue 2: Classification missing** - Pääluokka, Luokka, Alaluokka not syncing
3. **Issue 3: Partial date updates** - `valmistumisvuosi` doesn't update but `rakentaminen_pttyy` does
4. **Issue 4: District not updating** - Kaupunginosa fields not syncing

## Quick Start

```bash
# Build and run
docker-compose up --build

# Or run directly
docker build -t mock-pw .
docker run -p 8080:8080 -v $(pwd)/data:/data mock-pw
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

### ProjectWise Compatible

- `GET /pwapi/iModelConnectedProjects/{id}` - Get project metadata
- `POST /pwapi/iModelConnectedProjects/schemas/{schema}/classes/{class}/instances/{id}` - Update project

### Management

- `GET /` - Web UI
- `GET /api/projects` - List projects (JSON)
- `GET /api/sync-log` - Sync operations log
- `POST /api/reset` - Reset all data

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
