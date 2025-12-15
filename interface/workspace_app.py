"""
Kasm-style Workspaces Manager
A modern web interface for launching and managing Docker-based workspaces
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import docker
import yaml
import subprocess
import json
import uuid
import os
from pathlib import Path
from datetime import datetime, timedelta
import secrets
import threading
import time
import requests

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configuration - Absolute paths from script location
BASE_DIR = Path(__file__).resolve().parent  # interface directory
PROJECT_DIR = BASE_DIR.parent               # OSINT_platform directory
DATA_DIR = PROJECT_DIR / "data"
DOCKER_COMPOSE_FILE = PROJECT_DIR / "docker-compose-workspace.yml"
WORKSPACES_FILE = BASE_DIR / "workspaces.json"
DOCKER_SOCKET = "/var/run/docker.sock"

# VNC Configuration
VNC_BASE_PORT = 5900
NOVNC_PORT = 6080



# Initialize workspaces tracking
def load_workspaces():
    """Load saved workspaces"""
    if WORKSPACES_FILE.exists():
        with open(WORKSPACES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_workspaces(workspaces):
    """Save workspaces to file"""
    with open(WORKSPACES_FILE, "w") as f:
        json.dump(workspaces, f, indent=2)

def load_docker_compose():
    """Load docker-compose.yml"""
    if DOCKER_COMPOSE_FILE.exists():
        with open(DOCKER_COMPOSE_FILE, "r") as f:
            return yaml.safe_load(f)
    return {"services": {}}

def get_available_port(start_port=VNC_BASE_PORT, check_count=1000):
    """Find an available port with retry logic"""
    import socket
    port = start_port
    for attempt in range(check_count):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", port))
                s.close()
            # Double-check the port is still available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                result = s.connect_ex(("127.0.0.1", port))
                if result != 0:
                    return port
        except (OSError, socket.error):
            pass
        port += 1
    raise RuntimeError(f"No available ports found starting from {start_port}")

def is_port_available(port):
    """Check if a specific port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
            return True
    except OSError:
        return False

def container_name_exists(container_name):
    """Check if a container with this name already exists"""
    try:
        client = get_docker_client()
        if not client:
            return False
        containers = client.containers.list(all=True, filters={"name": f"^{container_name}$"})
        return len(containers) > 0
    except Exception:
        return False

def get_docker_client():
    """Get Docker client"""
    try:
        return docker.from_env()
    except Exception as e:
        print(f"Error connecting to Docker: {e}")
        return None

def verify_docker_connection():
    """Verify Docker is available and accessible"""
    try:
        client = docker.from_env()
        # Try to ping Docker to verify connection
        client.ping()
        print("[SUCCESS] Docker daemon is available and responding")
        return True
    except docker.errors.DockerException as e:
        print(f"\n{'='*60}")
        print("❌ ERROR: Cannot Connect to Docker Daemon")
        print(f"{'='*60}")
        print(f"Reason: {str(e)}")
        print(f"\nDetails: Docker daemon is not running or not accessible")
        print("\nPossible solutions:")
        print("  1. Start Docker daemon: sudo systemctl start docker")
        print("  2. Check Docker socket permissions: sudo usermod -aG docker $USER")
        print("  3. Verify Docker installation: docker --version")
        print("  4. Check Docker socket: ls -la /var/run/docker.sock")
        print(f"{'='*60}\n")
        return False
    except Exception as e:
        print(f"\n{'='*60}")
        print("❌ ERROR: Unexpected Error Connecting to Docker")
        print(f"{'='*60}")
        print(f"Reason: {str(e)}")
        print(f"Error Type: {type(e).__name__}")
        print(f"{'='*60}\n")
        return False

def create_workspace(service_name, workspace_name=None):
    """Create a new workspace instance using Docker SDK"""
    if workspace_name is None:
        workspace_name = f"{service_name}-{str(uuid.uuid4())[:8]}"
    
    # Validate workspace name format (alphanumeric, dash, underscore only)
    if not all(c.isalnum() or c in '-_' for c in workspace_name):
        return {"success": False, "error": "Workspace name can only contain alphanumeric characters, dashes, and underscores"}
    
    workspaces = load_workspaces()
    
    # Check if workspace already exists in tracking
    if workspace_name in workspaces:
        return {"success": False, "error": f"Workspace '{workspace_name}' already exists"}
    
    # Check if container with this name already exists in Docker
    if container_name_exists(workspace_name):
        return {"success": False, "error": f"Container named '{workspace_name}' already exists. Please remove it first or use a different name"}
    
    try:
        # Get Docker client
        client = get_docker_client()
        if not client:
            return {"success": False, "error": "Cannot connect to Docker daemon"}
        
        # Load compose config to get service details
        compose = load_docker_compose()
        if service_name not in compose.get("services", {}):
            return {"success": False, "error": f"Service '{service_name}' not found in docker-compose.yml"}
        
        service_config = compose["services"][service_name]
        
        # Get available ports for web VNC interface
        # We need to find a port for the container's port 3000
        web_port = get_available_port(3000)  # Start from 3000 and find next available
        if not is_port_available(web_port):
            return {"success": False, "error": f"Port {web_port} is not available"}
        

        print(f"[INFO] Creating workspace '{workspace_name}' for service '{service_name}'")
        print(f"[INFO] Allocated port - Web VNC: {web_port}")
        
        # Prepare container configuration
        image = service_config.get("image")
        if not image:
            return {"success": False, "error": f"Service '{service_name}' has no image defined"}
        
        # Pull image if not present
        print(f"[INFO] Ensuring image '{image}' is available...")
        try:
            client.images.get(image)
            print(f"[INFO] Image already present: {image}")
        except docker.errors.ImageNotFound:
            print(f"[INFO] Pulling image: {image}")
            try:
                # Set a timeout for pulling images (300 seconds = 5 minutes)
                client.images.pull(image, timeout=300)
                print(f"[SUCCESS] Image pulled: {image}")
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    return {"success": False, "error": f"Image pull timeout for '{image}' - took too long"}
                return {"success": False, "error": f"Failed to pull image '{image}': {error_msg}"}
        
        # Prepare environment variables
        env_vars = {}
        if "environment" in service_config:
            env_list = service_config["environment"]
            for env_var in env_list:
                if isinstance(env_var, str):
                    if "=" in env_var:
                        key, value = env_var.split("=", 1)
                        env_vars[key] = value
        
        # Prepare volumes
        volumes = {}
        if "volumes" in service_config:
            for volume in service_config["volumes"]:
                if isinstance(volume, str) and ":" in volume:
                    host_path, container_path = volume.split(":", 1)
                    # Handle relative paths - resolve relative to project directory
                    host_path = str(PROJECT_DIR) + host_path
                    #print(f"[DEBUG] Volume: '{host_path}' -> resolved: '{resolved_host_path}' -> container: '{container_path}'")
                    
                    volumes[str(host_path)] = {"bind": container_path, "mode": "rw"}
        
        # Ensure workspace-specific data directory
        workspace_data_dir = DATA_DIR / workspace_name
        workspace_data_dir.mkdir(parents=True, exist_ok=True)
        volumes[str(workspace_data_dir)] = {"bind": "/data", "mode": "rw"}


        # Prepare port mappings from compose file
        ports = {}
        if "ports" in service_config:
            for port_mapping in service_config["ports"]:
                if isinstance(port_mapping, str) and ":" in port_mapping:
                    host_port, container_port = port_mapping.split(":", 1)
                    ports[f"{container_port}/tcp"] = int(host_port)
        
        # Add mapping for web VNC port 3000 to available host port
        # This allows access to the container's web interface
        ports["3000/tcp"] = web_port
        
        # Create the container with explicit name
        print(f"[INFO] Creating Docker container '{workspace_name}'...")
        
        # Set a timeout for container creation (120 seconds = 2 minutes)
        try:
            container = client.containers.run(
                image,
                name=workspace_name,
                detach=True,
                environment=env_vars,
                volumes=volumes,
                ports=ports,
                shm_size=service_config.get("shm_size", "1gb"),
                security_opt=service_config.get("security_opt", []),
                cap_add=service_config.get("cap_add", []),
                restart_policy={"Name": "unless-stopped"} if service_config.get("restart") == "unless-stopped" else None,
                labels={
                    "workspace": workspace_name,
                    "service": service_name,
                    "created_by": "workspace_app"
                }
            )
        except requests.exceptions.Timeout:
            return {"success": False, "error": f"Container creation timeout - operation took too long. Please check Docker logs and try again."}
        except docker.errors.ContainerError as e:
            return {"success": False, "error": f"Container error during creation: {str(e)}"}
        
        print(f"[SUCCESS] Container created: {container.id[:12]} ({container.name})")
        
        # Wait a moment for container to stabilize
        time.sleep(2)
        
        # Verify container is running
        container.reload()
        if container.status != "running":
            # Try to get logs for debugging
            logs = container.logs().decode()
            print(f"[WARNING] Container status: {container.status}")
            print(f"[WARNING] Container logs:\n{logs}")
        
        # Save workspace metadata
        workspace_data = {
            "id": str(uuid.uuid4()),
            "name": workspace_name,
            "service": service_name,
            "status": container.status,
            "container_id": container.id[:12],
            "container_name": container.name,
            "image": image,
            "created": datetime.now().isoformat(),
            "web_port": web_port,
            "web_url": f"http://localhost:{web_port}",
            "last_accessed": datetime.now().isoformat()
        }
        
        workspaces[workspace_name] = workspace_data
        save_workspaces(workspaces)
        
        return {
            "success": True,
            "workspace": workspace_data,
            "message": f"Workspace '{workspace_name}' created successfully. Access at: http://localhost:{web_port}"
        }
    
    except docker.errors.ContainerError as e:
        print(f"[ERROR] Container error: {str(e)}")
        return {"success": False, "error": f"Container error: {str(e)}"}
    except docker.errors.ImageNotFound as e:
        print(f"[ERROR] Image not found: {str(e)}")
        return {"success": False, "error": f"Image not found: {str(e)}"}
    except docker.errors.APIError as e:
        print(f"[ERROR] Docker API error: {str(e)}")
        return {"success": False, "error": f"Docker API error: {str(e)}"}
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def delete_workspace(workspace_name):
    """Delete a workspace safely using Docker SDK"""
    try:
        print(f"[INFO] Deleting workspace '{workspace_name}'")
        
        client = get_docker_client()
        if not client:
            return {"success": False, "error": "Cannot connect to Docker daemon"}
        
        # Find container by name
        try:
            container = client.containers.get(workspace_name)
        except docker.errors.NotFound:
            # Container not found, just remove from tracking
            workspaces = load_workspaces()
            if workspace_name in workspaces:
                del workspaces[workspace_name]
                save_workspaces(workspaces)
                print(f"[INFO] Container '{workspace_name}' not found, removed from tracking")
            return {"success": True, "message": f"Workspace '{workspace_name}' cleaned up"}
        
        # Stop container if running
        if container.status == "running":
            print(f"[INFO] Stopping container '{workspace_name}'...")
            container.stop(timeout=10)
            print(f"[SUCCESS] Container stopped")
        
        # Remove container
        print(f"[INFO] Removing container '{workspace_name}'...")
        container.remove()
        print(f"[SUCCESS] Container removed")
        
        # Remove from tracking
        workspaces = load_workspaces()
        if workspace_name in workspaces:
            del workspaces[workspace_name]
            save_workspaces(workspaces)
            print(f"[SUCCESS] Workspace tracking removed for '{workspace_name}'")
        
        return {"success": True, "message": f"Workspace '{workspace_name}' deleted"}
    
    except docker.errors.APIError as e:
        print(f"[ERROR] Docker API error: {str(e)}")
        return {"success": False, "error": f"Docker API error: {str(e)}"}
    except Exception as e:
        print(f"[ERROR] Error deleting workspace: {str(e)}")
        return {"success": False, "error": str(e)}

def get_workspace_status(workspace_name):
    """Get status of a workspace using Docker SDK"""
    try:
        client = get_docker_client()
        if not client:
            return {"status": "unknown", "error": "Docker not available"}
        
        # Find container by exact name
        try:
            container = client.containers.get(workspace_name)
            return {
                "status": container.status,
                "running": container.status == "running",
                "id": container.id[:12],
                "name": container.name
            }
        except docker.errors.NotFound:
            return {"status": "stopped", "running": False}
    
    except Exception as e:
        return {"status": "unknown", "error": str(e)}

# Routes
@app.route("/")
def index():
    """Main dashboard"""
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    
    return render_template("index.html")

@app.route("/api/services")
def api_services():
    """Get available services"""
    compose = load_docker_compose()
    services = []
    
    for service_name, config in compose.get("services", {}).items():
        services.append({
            "name": service_name,
            "image": config.get("image", "unknown"),
            "description": config.get("description", ""),
            "icon": config.get("icon", "🐳")
        })
    
    return jsonify({"services": services})

@app.route("/api/workspaces")
def api_workspaces():
    """Get all workspaces"""
    workspaces = load_workspaces()
    workspace_list = []
    
    for ws_name, ws_data in workspaces.items():
        status = get_workspace_status(ws_name)
        ws_data["current_status"] = status.get("status", "unknown")
        workspace_list.append(ws_data)
    
    return jsonify({"workspaces": workspace_list})

@app.route("/api/workspace/<workspace_name>")
def api_workspace(workspace_name):
    """Get specific workspace details"""
    workspaces = load_workspaces()
    
    if workspace_name not in workspaces:
        return jsonify({"error": "Workspace not found"}), 404
    
    ws_data = workspaces[workspace_name]
    status = get_workspace_status(workspace_name)
    ws_data["current_status"] = status.get("status", "unknown")
    
    # Update last accessed
    ws_data["last_accessed"] = datetime.now().isoformat()
    workspaces[workspace_name] = ws_data
    save_workspaces(workspaces)
    
    return jsonify({"workspace": ws_data})

@app.route("/api/workspace/create", methods=["POST"])
def api_create_workspace():
    """Create a new workspace"""
    data = request.get_json()
    service_name = data.get("service")
    workspace_name = data.get("name")
    
    if not service_name:
        return jsonify({"error": "Service name required"}), 400
    
    result = create_workspace(service_name, workspace_name)
    
    if result["success"]:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@app.route("/api/workspace/<workspace_name>/delete", methods=["POST"])
def api_delete_workspace(workspace_name):
    """Delete a workspace"""
    result = delete_workspace(workspace_name)
    
    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route("/api/workspace/<workspace_name>/logs")
def api_workspace_logs(workspace_name):
    """Get workspace container logs"""
    try:
        client = get_docker_client()
        if not client:
            return jsonify({"error": "Docker not available"}), 500
        
        # Get container by name
        try:
            container = client.containers.get(workspace_name)
        except docker.errors.NotFound:
            return jsonify({"error": "Container not found"}), 404
        
        logs = container.logs(tail=100).decode()
        return jsonify({"logs": logs})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/workspace/<workspace_name>")
def workspace_view(workspace_name):
    """Workspace view with embedded VNC"""
    workspaces = load_workspaces()
    
    if workspace_name not in workspaces:
        return "Workspace not found", 404
    
    ws_data = workspaces[workspace_name]
    status = get_workspace_status(workspace_name)
    
    return render_template(
        "workspace.html",
        workspace=ws_data,
        status=status.get("status"),
        vnc_port=ws_data.get("vnc_port")
    )

@app.route("/api/health")
def health():
    """Health check"""
    docker_available = get_docker_client() is not None
    return jsonify({
        "status": "healthy" if docker_available else "degraded",
        "docker": docker_available
    })

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Workspaces Application")
    print("="*60)
    
    # Check Docker connectivity before starting
    print("\n[*] Checking Docker connectivity...")
    if not verify_docker_connection():
        print("\n[FATAL] Cannot start application without Docker access")
        print("Please resolve Docker issues and try again.")
        import sys
        sys.exit(1)
    
    print("\n[*] Initializing Flask application...")
    print("[*] Loading workspaces metadata...")
    try:
        workspaces = load_workspaces()
        print(f"[SUCCESS] Loaded {len(workspaces)} workspace(s)")
    except Exception as e:
        print(f"[WARNING] Could not load workspaces: {e}")
    
    print("\n[*] Loading Docker Compose configuration...")
    try:
        compose = load_docker_compose()
        services = compose.get("services", {})
        print(f"[SUCCESS] Found {len(services)} service(s): {', '.join(services.keys())}")
    except Exception as e:
        print(f"[WARNING] Could not load Docker Compose: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Application Ready!")
    print(f"{'='*60}")
    print("📍 Web Interface: http://localhost:5000")
    print("📊 API Health Check: http://localhost:5000/api/health")
    print("🔧 Press Ctrl+C to shutdown")
    print(f"{'='*60}\n")
    
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n[*] Shutdown signal received")
        print("[*] Cleaning up and exiting...")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during execution: {e}")
        import sys
        sys.exit(1)
