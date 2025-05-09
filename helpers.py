import platform
import subprocess
import importlib.metadata
import distro # You'll need to install this: pip install distro

def get_os_info():
    """
    Retrieves basic OS and kernel information.
    """
    info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
    }
    if info['system'] == 'Linux':
        try:
            info['distro_name'] = distro.name(pretty=True)
            info['distro_id'] = distro.id()
            info['distro_version'] = distro.version(pretty=True)
            info['distro_codename'] = distro.codename()
        except Exception: # Fallback if distro lib fails or not Linux
            info['distro_name'] = 'N/A (distro lib error or not Linux)'
            info['distro_id'] = 'unknown' # Important for package manager detection
    elif info['system'] == 'Darwin': # macOS
        try:
            mac_ver = platform.mac_ver()
            info['distro_name'] = f"macOS {mac_ver[0]}"
            info['distro_id'] = 'macos' # For potential future use
        except Exception:
            info['distro_name'] = 'macOS (version unavailable)'
            info['distro_id'] = 'macos'
    elif info['system'] == 'Windows':
        info['distro_name'] = f"Windows {info['release']}"
        info['distro_id'] = 'windows'
    else:
        info['distro_name'] = 'Unknown OS'
        info['distro_id'] = 'unknown'

    return info

def get_python_package_version(package_name):
    """
    Retrieves the version of an installed Python package.
    Uses importlib.metadata (Python 3.8+).
    """
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Not Found"
    except Exception as e:
        return f"Error: {str(e)}"

def get_system_package_version(package_name, os_id='unknown'):
    """
    Retrieves the version of an installed system package.
    This is OS-dependent.
    """
    command = []
    if not package_name: # Safety check
        return "N/A (No package name)"

    # Normalize os_id to lowercase for reliable matching
    os_id_lower = os_id.lower()

    if any(dist in os_id_lower for dist in ['ubuntu', 'debian', 'mint']):
        command = ['dpkg-query', '-W', '-f=${Version}', package_name]
    elif any(dist in os_id_lower for dist in ['centos', 'rhel', 'fedora', 'almalinux', 'rocky']):
        command = ['rpm', '-q', '--qf', '%{VERSION}', package_name]
    elif 'arch' in os_id_lower:
        command = ['pacman', '-Q', package_name] # Output needs parsing: package_name version
    elif 'macos' in os_id_lower: # Example for Homebrew, adjust if using MacPorts etc.
        # This assumes the package might be installed via Homebrew.
        # A more robust solution for macOS might involve checking multiple package managers
        # or using system APIs if available for specific software.
        command = ['brew', 'info', '--json=v2', package_name] # Output needs JSON parsing
    else:
        return "Unsupported OS for system package check or OS ID not recognized"

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=5) # 5-second timeout

        if process.returncode == 0:
            version_output = stdout.strip()
            if 'arch' in os_id_lower and version_output:
                # Pacman output is "package_name version", extract version
                parts = version_output.split()
                if len(parts) > 1 and parts[0] == package_name:
                    return parts[1]
                return version_output # Or "Could not parse Arch output"
            elif 'macos' in os_id_lower and version_output:
                # brew info --json=v2 <package>
                # For a single package, it returns a dict with a "formulae" or "casks" key
                # which is a list. We take the first one.
                import json
                try:
                    data = json.loads(version_output)
                    if data.get('formulae') and data['formulae']:
                        return data['formulae'][0]['versions']['stable']
                    elif data.get('casks') and data['casks']:
                         # Cask versions are often just the app version string
                        return data['casks'][0]['version']
                    return "Version not found in brew output"
                except json.JSONDecodeError:
                    return "Failed to parse brew JSON output"
                except KeyError:
                    return "Version info not in expected brew JSON structure"
            return version_output if version_output else "Not Found (empty output)"
        else:
            # Common errors: package not found, command not found
            if "not found" in stderr.lower() or "no packages found" in stderr.lower() or "error: package" in stderr.lower() or process.returncode == 1: # pacman returns 1 if not found
                return "Not Found"
            return f"Error (code {process.returncode}): {stderr.strip()}"
    except FileNotFoundError:
        return f"Command not found ({command[0]}) - Is the package manager installed and in PATH?"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Execution error: {str(e)}"

if __name__ == '__main__':
    # For testing the helper functions directly
    print("--- OS Info ---")
    os_info = get_os_info()
    for key, value in os_info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")

    print("\n--- Python Package Versions ---")
    print(f"distro: {get_python_package_version('distro')}")
    print(f"Flask: {get_python_package_version('flask')}")
    print(f"nonexistent_package: {get_python_package_version('nonexistent_python_package')}")

    print("\n--- System Package Versions (example for current OS) ---")
    current_os_id = os_info.get('distro_id', 'unknown')
    # Common packages that might exist - replace with relevant ones for your testing
    # On Linux:
    if current_os_id not in ['windows', 'macos', 'unknown']:
        print(f"bash (on {current_os_id}): {get_system_package_version('bash', current_os_id)}")
        print(f"openssl (on {current_os_id}): {get_system_package_version('openssl', current_os_id)}")
        print(f"nginx (on {current_os_id}): {get_system_package_version('nginx', current_os_id)}") # May not be installed
        print(f"nonexistent (on {current_os_id}): {get_system_package_version('nonexistentsystempackage', current_os_id)}")
    elif current_os_id == 'macos':
        print(f"git (on {current_os_id}): {get_system_package_version('git', current_os_id)}") # Commonly installed via brew
        print(f"nonexistent (on {current_os_id}): {get_system_package_version('nonexistentsystempackage', current_os_id)}")
    else:
        print("Skipping system package tests for Windows or Unknown OS in this example.")
