import streamlit as st
import subprocess
import os
from pathlib import Path

# Base path for generated environment files
env_dir = Path("./env_files")
env_dir.mkdir(exist_ok=True)

# Static PUID and PGID
PUID = "1000"
PGID = "1000"

# Dropdown options for Time Zones and Locales
TIME_ZONES = [
    "Etc/UTC", "America/New_York", "Europe/Moscow", "Asia/Kolkata", "Australia/Sydney"
]
LOCALES = [
    "en_US.UTF-8", "ru_RU.UTF-8", "fr_FR.UTF-8", "zh_CN.UTF-8", "es_ES.UTF-8"
]

# Sidebar: General configuration
st.sidebar.header("General Configuration")
instance_name = st.sidebar.text_input("Instance Name", "browser_stack")
timezone = st.sidebar.selectbox("Time Zone (TZ)", TIME_ZONES)
locale = st.sidebar.selectbox("Locale (LC_ALL)", LOCALES)

# Sidebar: Service Selection
st.sidebar.header("Select Services to Deploy")
services = {
    "firefox": {
        "name": "Firefox",
        "volumes": {"FIREFOX_BOOKMARKS": "./bookmarks", "FIREFOX_PREFS": "./firefox/preferences"},
        "ports": {"FIREFOX_PORT1": "3000", "FIREFOX_PORT2": "4000"},
    },
    "chromium": {
        "name": "Chromium",
        "volumes": {"CHROMIUM_BOOKMARKS": "./chromium/bookmarks"},
        "ports": {"CHROMIUM_PORT1": "3001", "CHROMIUM_PORT2": "4001"},
    },
    "tor": {
        "name": "Tor",
        "volumes": {"TOR_BOOKMARKS": "./tor/bookmarks"},
        "ports": {"TOR_PORT1": "3002"},
    },
    "telegram": {"name": "Telegram", "ports": {"TELEGRAM_PORT1": "3003"}},
    "keybase": {"name": "Keybase", "ports": {"KEYBASE_PORT1": "3004"}},
}

selected_services = {}
for service, config in services.items():
    if st.sidebar.checkbox(f"Enable {config['name']}"):
        selected_services[service] = config

# Deploy button
if st.sidebar.button("Deploy"):
    if selected_services:
        # Generate the .env file
        env_file_path = env_dir / f"{instance_name}.env"
        with open(env_file_path, "w") as f:
            f.write(f"PUID={PUID}\n")
            f.write(f"PGID={PGID}\n")
            f.write(f"TZ={timezone}\n")
            f.write(f"LC_ALL={locale}\n")
            # Add service-specific environment variables
            for service, config in selected_services.items():
                for var, value in config.get("volumes", {}).items():
                    f.write(f"{var}={value}\n")
                for var, value in config.get("ports", {}).items():
                    f.write(f"{var}={value}\n")

        # Generate Docker Compose command
        try:
            subprocess.run(
                ["docker-compose", "-p", instance_name, "--env-file", str(env_file_path), "up", "-d"] +
                [service for service in selected_services],
                check=True,
            )
            st.success(f"Instance '{instance_name}' deployed successfully with selected services!")
        except subprocess.CalledProcessError as e:
            st.error(f"Failed to deploy instance: {e}")
    else:
        st.warning("Please select at least one service to deploy.")

# Display currently active instances
st.header("Active Instances")
try:
    active_containers = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"]).decode().splitlines()
    if active_containers:
        for container in active_containers:
            st.write(f"Container: {container}")
            # Stop button
            if st.button(f"Stop {container}"):
                subprocess.run(["docker", "stop", container])
                st.success(f"Stopped {container}")
    else:
        st.write("No active instances.")
except Exception as e:
    st.error(f"Failed to retrieve active instances: {e}")
