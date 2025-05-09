# Host Details Viewer

A simple Python Flask web application to display live host details like OS information, kernel version, and versions of configured Python and system packages.

## Features

* Displays detailed OS and kernel information.
* Shows versions of specified Python packages.
* Shows versions of specified system packages (supports Debian/Ubuntu, RHEL/CentOS/Fedora, Arch, macOS with Homebrew).
* Package lists are configurable via `config.json`.
* Simple, clean web interface.

## Project Structure


## Prerequisites

* Python 3.8 or higher (due to `importlib.metadata`)
* `pip` (Python package installer)
* For system package version checking:
    * On Debian/Ubuntu: `dpkg`
    * On RHEL/CentOS/Fedora: `rpm`
    * On Arch Linux: `pacman`
    * On macOS: `brew` (if you want to check Homebrew packages)

## Setup and Local Development

1.  **Clone the repository (or create the files as described):**
    ```bash
    # If you have it in a git repo:
    # git clone <your-repo-url>
    # cd host_details_app
    ```

2.  **Create a Python virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install Flask gunicorn distro
    ```

4.  **Configure Packages (Optional):**
    Edit `config.json` to add or remove Python and system packages you want to monitor.

5.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
    The application will be available at `http://127.0.0.1:5000` or `http://localhost:5000`.

## Deployment

For production, do NOT use the Flask development server. Instead, use a WSGI server like Gunicorn, preferably behind a reverse proxy like Nginx or Apache.

### Using Gunicorn

1.  **Install Gunicorn** (if not already installed in your environment):
    ```bash
    pip install gunicorn
    ```

2.  **Run with Gunicorn:**
    Navigate to your `host_details_app` directory. The Flask app instance is named `app` in `app.py`.
    ```bash
    gunicorn --workers 4 --bind 0.0.0.0:8000 app:app
    ```
    * `--workers 4`: Adjust the number of worker processes based on your server's CPU cores (a common starting point is `2 * num_cores + 1`).
    * `--bind 0.0.0.0:8000`: Binds Gunicorn to port 8000 on all network interfaces. Choose a port that isn't in use.
    * `app:app`: Tells Gunicorn to look for an object named `app` inside the `app.py` module.

    You can also bind to a Unix socket, which is common when using a reverse proxy on the same machine:
    ```bash
    gunicorn --workers 4 --bind unix:/tmp/hostdetails.sock app:app
    # Ensure the directory for the socket is writable by the Gunicorn user.
    # /run/your_app_name/socket.sock is often preferred over /tmp for production.
    ```

### Option 1: Deploying with Gunicorn and Nginx (Recommended for Production)

Nginx will act as a reverse proxy, handling incoming HTTP(S) requests and forwarding them to Gunicorn.

1.  **Install Nginx:**
    ```bash
    sudo apt update # For Debian/Ubuntu
    sudo apt install nginx
    # Or: sudo yum install nginx (for RHEL/CentOS)
    ```

2.  **Configure Nginx:**
    Create a new Nginx server block configuration file. For example, `/etc/nginx/sites-available/host_details`:
    ```nginx
    server {
        listen 80; # Or 443 if you have SSL
        server_name your_domain_or_server_ip; # e.g., details.example.com or your IP

        # Optional: Add access and error logs
        access_log /var/log/nginx/host_details_access.log;
        error_log /var/log/nginx/host_details_error.log;

        location /static {
            # Path to your static files
            alias /path/to/your/host_details_app/static;
        }

        location / {
            proxy_pass [http://127.0.0.1:8000](http://127.0.0.1:8000); # If Gunicorn is on port 8000
            # If using a Unix socket:
            # proxy_pass http://unix:/tmp/hostdetails.sock;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    ```
    * Replace `/path/to/your/host_details_app/` with the actual absolute path to your application.
    * Replace `your_domain_or_server_ip` with your server's public IP address or domain name.
    * If Gunicorn is listening on a Unix socket, change `proxy_pass` accordingly.

3.  **Enable the Nginx configuration:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/host_details /etc/nginx/sites-enabled/
    sudo nginx -t # Test Nginx configuration
    sudo systemctl restart nginx # Or: sudo service nginx restart
    ```

4.  **Ensure Gunicorn is running** (e.g., using `systemd` or a process manager like Supervisor to keep it running in the background).

    **Example `systemd` service file (`/etc/systemd/system/host_details.service`):**
    ```ini
    [Unit]
    Description=Gunicorn instance for Host Details Viewer
    After=network.target

    [Service]
    User=your_user                 # Replace with the user Gunicorn should run as
    Group=www-data               # Or your_user's group
    WorkingDirectory=/path/to/your/host_details_app
    Environment="PATH=/path/to/your/host_details_app/venv/bin" # Path to virtualenv bin
    ExecStart=/path/to/your/host_details_app/venv/bin/gunicorn --workers 3 --bind unix:/run/host_details/hostdetails.sock app:app
    # Ensure /run/host_details directory exists and is writable by 'your_user' or 'www-data'
    # Create it: sudo mkdir /run/host_details; sudo chown your_user:www-data /run/host_details

    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    * Replace `your_user`, `/path/to/your/host_details_app`, and paths to Gunicorn/Python in `venv`.
    * Then:
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl start host_details
        sudo systemctl enable host_details # To start on boot
        sudo systemctl status host_details
        ```

### Option 2: Deploying with Gunicorn and Apache

Apache can also act as a reverse proxy using `mod_proxy`.

1.  **Install Apache and `mod_proxy`:**
    ```bash
    sudo apt update # For Debian/Ubuntu
    sudo apt install apache2
    sudo a2enmod proxy proxy_http proxy_balancer lbmethod_byrequests # Enable proxy modules
    sudo systemctl restart apache2
    # Or: sudo yum install httpd (for RHEL/CentOS)
    ```

2.  **Configure Apache:**
    Create a new Apache virtual host configuration file. For example, `/etc/apache2/sites-available/host_details.conf`:
    ```apache
    <VirtualHost *:80>
        ServerName your_domain_or_server_ip

        # Optional: Add access and error logs
        ErrorLog ${APACHE_LOG_DIR}/host_details_error.log
        CustomLog ${APACHE_LOG_DIR}/host_details_access.log combined

        # Proxy requests to Gunicorn
        ProxyPreserveHost On
        ProxyPass /static ! # Don't proxy static files if serving them directly
        ProxyPass / [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
        ProxyPassReverse / [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

        # If Gunicorn is on a Unix socket (requires mod_proxy_unix):
        # sudo apt install libapache2-mod-proxy-unix # (or equivalent for your distro)
        # sudo a2enmod proxy_unix
        # ProxyPass / unix:/tmp/hostdetails.sock|http://localhost/

        # Serve static files directly via Apache for better performance
        Alias /static /path/to/your/host_details_app/static
        <Directory /path/to/your/host_details_app/static>
            Require all granted
        </Directory>

    </VirtualHost>
    ```
    * Replace paths and server name.
    * Ensure Gunicorn is running and listening on `127.0.0.1:8000` or the specified socket.

3.  **Enable the Apache configuration:**
    ```bash
    sudo a2ensite host_details.conf
    sudo systemctl reload apache2 # Or: sudo service apache2 reload
    ```
    Ensure Gunicorn is running (e.g., using `systemd` as described in the Nginx section).

## Customization

* **Packages**: Modify `config.json` to change which Python and system packages are monitored.
* **Styling**: Edit `static/style.css` to change the appearance.
* **HTML**: Modify `templates/index.html` to alter the page structure or content.

## Troubleshooting

* **"Command not found" for system packages**: Ensure the relevant package manager (dpkg, rpm, pacman, brew) is installed and in the system's PATH for the user running the Flask/Gunicorn process.
* **"Permission denied" for socket file**: Ensure the user running Gunicorn has write permissions to the directory where the Unix socket is created, and the user running Nginx/Apache has read/write permissions to the socket file itself. Common practice is to create a dedicated directory in `/run/` for the socket.
* **Python Package "Not Found"**: Ensure the package is installed in the Python environment where the Flask application (and Gunicorn) is running. If using virtual environments, activate the correct one.
* **Check Gunicorn/Web Server Logs**:
    * Gunicorn output (if run directly)
    * Nginx: `/var/log/nginx/error.log` and `/var/log/nginx/access.log` (or your custom log paths).
    * Apache: `/var/log/apache2/error.log` and `/var/log/apache2/access.log` (or your custom log paths).
    * Systemd service logs: `sudo journalctl -u host_details.service`

