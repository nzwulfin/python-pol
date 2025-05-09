import json
import os
from flask import Flask, render_template
from helpers import get_os_info, get_python_package_version, get_system_package_version

app = Flask(__name__)

# Path to the config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

def load_config():
    """Loads the configuration from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: {CONFIG_FILE} not found. Returning empty config.")
        return {"python_packages": [], "system_packages": []}
    except json.JSONDecodeError:
        print(f"Error: Could not decode {CONFIG_FILE}. Returning empty config.")
        return {"python_packages": [], "system_packages": []}

@app.route('/')
def index():
    """Main route to display host details."""
    config = load_config()
    os_details = get_os_info()
    
    # Get OS ID for system package version checking
    current_os_id = os_details.get('distro_id', 'unknown')
    if os_details.get('system') == 'Darwin': # Consolidate macOS check
        current_os_id = 'macos'
    elif os_details.get('system') == 'Windows':
        current_os_id = 'windows'


    python_pkg_versions = []
    if config.get("python_packages"):
        for pkg_name in config["python_packages"]:
            python_pkg_versions.append({
                "name": pkg_name,
                "version": get_python_package_version(pkg_name)
            })

    system_pkg_versions = []
    if config.get("system_packages"):
        for pkg_name in config["system_packages"]:
            system_pkg_versions.append({
                "name": pkg_name,
                "version": get_system_package_version(pkg_name, current_os_id)
            })
            
    # Current date for the page
    from datetime import datetime
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        'index.html',
        os_details=os_details,
        python_packages=python_pkg_versions,
        system_packages=system_pkg_versions,
        current_time=current_time
    )

if __name__ == '__main__':
    # For local development:
    # In a production environment, you'll use a WSGI server like Gunicorn.
    app.run(debug=True, host='0.0.0.0', port=5000)
