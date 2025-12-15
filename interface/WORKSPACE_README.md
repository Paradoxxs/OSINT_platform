# Kasm-Style Workspaces Platform

A modern, containerized workspace management system similar to Kasm Workspaces. Launch, manage, and access Docker-based services through a sleek web interface with support for multiple concurrent instances.

## Features

### 🎯 **Modern Web Interface**
- Clean, dark-themed dashboard (inspired by Kasm Workspaces)
- Responsive design that works on desktop and tablet
- Real-time workspace status updates
- Instant workspace creation

### 🚀 **Workspace Management**
- **Create workspaces** from any available Docker service
- **Multiple instances** of the same service (e.g., 3 separate Firefox workspaces)
- **Auto-naming** or custom workspace names
- **Quick connect** via embedded VNC viewer
- **Automatic tracking** of all workspace metadata

### 💻 **Access Methods**
- Web-based VNC viewer (noVNC) for direct access
- Direct VNC port forwarding for external tools
- Container logs viewing
- Resource monitoring per workspace

### 🔧 **Service Discovery**
- Automatic service detection from `docker-compose.yml`
- Service icons and descriptions
- One-click workspace launch
- Support for any Docker image

### 📊 **Workspace Tracking**
- Persistent workspace metadata
- Creation and access timestamps
- Service association
- Status monitoring

## Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Linux/macOS or WSL2 on Windows

### Setup Steps

1. **Install dependencies:**
```bash
cd /home/atj/projects/OSINT_platform/interface
pip install -r requirements.txt
```

2. **Configure Docker Compose** (if needed):
Ensure your `docker-compose.yml` includes services with proper configurations.

3. **Start the application:**
```bash
python workspace_app.py
```

The interface will be available at `http://localhost:5000`

## Usage Guide

### Creating a Workspace

1. Click **"New Workspace"** button (top right)
2. Select a service from the dropdown
3. (Optional) Enter a custom workspace name
4. Click **"Create Workspace"**
5. Wait for the container to start (~5-30 seconds depending on image)

### Accessing a Workspace

1. Go to **"Active Workspaces"** tab
2. Find your workspace in the grid
3. Click **"Connect"** button
4. The VNC viewer opens in a new panel
5. Interact with your desktop environment

### Managing Multiple Instances

**Example: Three separate Firefox environments**

```
Instance 1: "firefox-work"     → Firefox for productivity
Instance 2: "firefox-testing"  → Firefox for web testing
Instance 3: "firefox-research" → Firefox for research
```

All three run simultaneously with isolated environments!

### Viewing Workspace Details

- Click the **ℹ️** icon on any workspace card
- View workspace name, service, status, ports, and creation date
- Useful for debugging or sharing connection details

### Stopping/Deleting a Workspace

1. Click the **🗑️** trash icon
2. Confirm deletion
3. Workspace is removed and Docker container is stopped

### Viewing Logs

In the workspace sidebar:
1. Click **"Show Logs"** button
2. Last 100 lines of container logs appear
3. Useful for debugging startup issues

## Architecture

### Backend (Flask)
- **`workspace_app.py`** - Main Flask application
- REST API for workspace management
- Docker API integration
- Workspace metadata persistence

### Frontend
- **`templates/index.html`** - Main dashboard
- **`templates/workspace.html`** - Workspace viewer
- **`static/style.css`** - Modern UI styling
- **`static/app.js`** - Dashboard functionality
- **`static/workspace.js`** - VNC integration

### Data Storage
- **`workspaces.json`** - Persistent workspace metadata (auto-created)

### Docker Integration
- Uses Docker Python SDK for container management
- Docker Compose for service orchestration
- Native support for all compose configurations

## API Endpoints

### Services
- `GET /api/services` - List available services

### Workspaces
- `GET /api/workspaces` - List all workspaces
- `GET /api/workspace/<name>` - Get workspace details
- `POST /api/workspace/create` - Create new workspace
- `POST /api/workspace/<name>/delete` - Delete workspace
- `GET /api/workspace/<name>/logs` - Get container logs

### Web Pages
- `GET /` - Main dashboard
- `GET /workspace/<name>` - Workspace viewer with VNC

## Configuration

### Adding Service Icons/Descriptions

Edit your `docker-compose.yml` and add labels:

```yaml
services:
  firefox:
    image: lscr.io/linuxserver/firefox:latest
    labels:
      - "icon=🔥"
      - "description=Firefox Browser"
```

### Environment Variables (Optional)

Add to your service in `docker-compose.yml`:

```yaml
environment:
  - DISPLAY=:99
  - VNC_ENABLED=true
```

## File Structure

```
interface/
├── workspace_app.py          # Flask application
├── requirements.txt          # Python dependencies
├── workspaces.json          # Auto-created workspace tracking
├── templates/
│   ├── index.html           # Dashboard
│   └── workspace.html       # Workspace viewer
└── static/
    ├── style.css            # Styling
    ├── app.js               # Dashboard logic
    └── workspace.js         # VNC viewer integration
```

## Common Issues & Solutions

### **Workspaces won't start**
- Check Docker daemon is running: `docker ps`
- Verify compose file exists: `../docker-compose.yml`
- Check logs: `docker logs <container_name>`

### **Can't connect to workspace**
- Ensure container is fully started (wait 5-10 seconds)
- Check if VNC port is accessible: `netstat -tuln | grep <port>`
- Try refreshing the page

### **Port conflicts**
- Application auto-selects available ports
- If issues persist, restart Docker daemon
- Check for zombie containers: `docker ps -a | grep Exit`

### **Lost workspace metadata**
- Delete `workspaces.json` to reset
- Running workspaces will be re-discovered on refresh

## Performance Tips

- **Max workspaces per system**: Depends on available resources
- **Recommended max**: 5-10 concurrent workspaces on 4GB+ RAM
- **Monitor usage**: Check Docker stats in sidebar
- **Clean up**: Delete unused workspaces to free resources

## Security Considerations

⚠️ **Important Notes:**
- This interface provides direct access to services
- Implement authentication for production use
- Restrict access to trusted networks
- Consider using nginx reverse proxy with SSL/TLS
- Use Docker secrets for sensitive data

## Advanced Usage

### Custom Service Names Pattern

Use descriptive names for organization:
- `service-region`: `firefox-us`, `firefox-eu`
- `service-version`: `app-v1`, `app-v2`
- `service-purpose`: `test-linux`, `prod-linux`

### Connecting External Tools

Get VNC port from workspace details modal:
```bash
# VNC client connection example
vncviewer localhost:5900
```

### Docker Compose Troubleshooting

```bash
# Check running workspaces
docker ps | grep workspace-

# View workspace logs
docker-compose -p workspace-name logs

# Manually stop workspace
docker-compose -p workspace-name down
```

## Future Enhancements

- [ ] User authentication
- [ ] SSL/TLS encryption
- [ ] Workspace scheduling (auto-start/stop)
- [ ] Resource limits per workspace
- [ ] Snapshot/backup functionality
- [ ] Workspace templates
- [ ] Real-time resource graphs
- [ ] Email notifications

## Support & Troubleshooting

For issues:
1. Check application logs: Check browser console (F12)
2. View Docker logs: `docker logs <container>`
3. Verify compose file: `docker-compose config`
4. Check port availability: `netstat -tuln`

## License

See main OSINT_platform repository

## Related Documentation

- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Kasm Workspaces](https://www.kasmweb.com/)
- [noVNC Documentation](https://novnc.io/)
