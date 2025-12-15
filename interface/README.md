# Interface Application Structure

## Overview
The interface folder contains a modern Flask-based workspace management system for Docker services.

## Files & Directories

### Core Application
- **`workspace_app.py`** - Main Flask application (5000 port)
  - REST API endpoints for workspace management
  - Docker integration and orchestration
  - Workspace metadata tracking
  - Container lifecycle management

### Web Interface
- **`templates/`** - HTML templates
  - `index.html` - Main dashboard with tabs for active workspaces and available services
  - `workspace.html` - Individual workspace viewer with VNC integration

- **`static/`** - Frontend assets
  - `style.css` - Modern dark-themed styling
  - `app.js` - Dashboard functionality and API interactions
  - `workspace.js` - VNC viewer integration

### Configuration & Dependencies
- **`requirements.txt`** - Python dependencies (Flask, Docker SDK, PyYAML, etc.)
- **`Pipfile`** / **`Pipfile.lock`** - Pipenv configuration
- **`docker-compose.yml`** - Docker setup for interface container (if needed)
- **`dockerfile`** - Container image definition
- **`WORKSPACE_README.md`** - Comprehensive documentation

### Data Files
- **`workspaces.json`** - Auto-created workspace metadata tracking
- **`encrypted_database.sqlite`** - Optional encrypted database

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask application
python workspace_app.py

# Access web interface
# Visit: http://localhost:5000
```

## Architecture

### Backend (Flask)
```
workspace_app.py
├── Routes
│   ├── GET  /                          → Main dashboard
│   ├── GET  /workspace/<name>          → Workspace viewer
│   ├── GET  /api/services              → List services
│   ├── GET  /api/workspaces            → List workspaces
│   ├── POST /api/workspace/create      → Create workspace
│   ├── POST /api/workspace/<id>/delete → Delete workspace
│   └── GET  /api/workspace/<id>/logs   → Container logs
└── Functions
    ├── load_workspaces()               → Load metadata
    ├── save_workspaces()               → Save metadata
    ├── create_workspace()              → Create container
    ├── delete_workspace()              → Remove container
    └── get_workspace_status()          → Check status
```

### Frontend (HTML/CSS/JS)
```
index.html
├── Header (Logo, New Workspace button)
├── Tabs
│   ├── Active Workspaces (grid view)
│   └── Available Services (grid view)
├── Modals
│   ├── New Workspace (create form)
│   └── Workspace Details (info display)
└── Sidebar (Dashboard options)

workspace.html
├── Sidebar (Workspace info & controls)
└── Main (VNC viewer embedded)
```

## Dependencies

- **flask** - Web framework
- **flask-cors** - CORS support
- **docker** - Docker Python SDK
- **PyYAML** - YAML parsing for docker-compose
- **pysqlcipher3** - Optional encrypted database
- **pysqlitecipher** - Optional SQLite cipher

## No Longer Used

The following Streamlit-based files have been removed:
- ❌ `app.py` (old Streamlit app)
- ❌ `test.py` (old Streamlit test)
- ❌ `basic.py` (old Streamlit basic app)
- ❌ `dashboard.py` (old Streamlit dashboard)
- ❌ `DASHBOARD_README.md` (old Streamlit docs)

## Key Features

✅ Modern dark-themed web interface
✅ Multi-tab workspace management
✅ One-click service deployment
✅ Multiple concurrent instances of same service
✅ Real-time status monitoring
✅ Container log viewing
✅ Automatic port allocation
✅ Container name conflict detection
✅ Persistent metadata tracking
✅ RESTful API design

## Environment

- Python 3.8+
- Docker & Docker Compose
- Linux/macOS or WSL2 on Windows
- No external dependencies beyond Python packages

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Start app: `python workspace_app.py`
3. Open browser: `http://localhost:5000`
4. Create your first workspace!
