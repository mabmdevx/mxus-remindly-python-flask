# Remindly
A reminder app to help you keep track of your tasks, events, appointments, document validity, renewals and more.

## Features
- Create and manage reminders
- Create recurring and non-recurring reminders
- Share reminders with others
- Receive notifications when your reminders and shared reminders are due

## Tech Stack
- Tech Stack: Python Flask, Bootstrap, HTML, CSS, JS
- Database: MySQL
- WebApp Architecture: Postback
- Tools/Services used:
    - Statcounter

## Setup the app in development mode

### Create a virtual environment
```
# For Unix environment
python -m venv .venv
source .venv/bin/activate
```

```
# For Windows environment
python -m venv .venv
.venv\Scripts\activate
```

### Install dependencies
```
pip install -r requirements.txt
```

### Create the config file
```
cp env.example .env
```

### Running the app in development mode
```
flask --app app:init_app run --debug
```

Application will start by default on http://localhost:5000

---

## Setup the app in production mode

Flask app setup using Gunicorn in production mode

### About Gunicorn
```
Type: WSGI HTTP Server
Best for: Traditional synchronous Python web frameworks (Flask, Django without ASGI, Pyramid, etc.).
Protocol: Implements WSGI (Web Server Gateway Interface).
Concurrency Model: Uses multiple worker processes (prefork model).
```

### Create the config file
```
cp env.example .env
```

### Configure the values
```
vim .env
```

```
FLASK_ENV=production
```

### Setup the virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Create the database
```
mysql -u root -p
CREATE DATABASE remindly CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'remindly'@'localhost' IDENTIFIED BY 'yourpassword';
GRANT ALL PRIVILEGES ON remindly.* TO 'remindly'@'localhost';
FLUSH PRIVILEGES;
```

### Running the app in production mode
Note: Recommended to run the app using Gunicorn as a WSGI server managed by Systemd.

If you want to run the app directly:
```
gunicorn -w 2 -b 127.0.0.1:8002 app.wsgi:app
```
OR
if you want to use a gunicorn config file:
Run from source directory:
```
gunicorn -c ../config/gunicorn/gunicorn_config.py app.wsgi:app
```
### Create a system user and group for the app
```
sudo adduser --system --no-create-home --group remindly
```

### Create a log directory
```
sudo mkdir -p /var/log/remindly
chown -R remindly:remindly /var/log/remindly
```

### Configure Systemd to manage Gunicorn
```
sudo nano /etc/systemd/system/remindly.service
```

```
[Unit]
Description=Gunicorn instance to serve Remindly
After=network.target

[Service]
User=yourusername
Group=www-data
WorkingDirectory=/opt/projects/remindly
Environment="PATH=/opt/projects/remindly/.venv/bin"
ExecStart=/opt/projects/remindly/.venv/bin/gunicorn -c /opt/projects/remindly/config/gunicorn_config.py wsgi:app
Restart=always
RestartSec=5
KillSignal=SIGQUIT
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable remindly
sudo systemctl start remindly
```

### Setup the Nginx reverse proxy
```
sudo nano /etc/nginx/sites-available/remindly
```
```
server {
    listen 80;
    server_name remindly.yourdomain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

}
```

```
sudo ln -s /etc/nginx/sites-available/remindly /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Enable HTTPS
```
sudo certbot --nginx -d remindly.yourdomain.com
sudo systemctl restart nginx
```

### How to check logs using journalctl
```
journalctl -u remindly
journalctl -u remindly -n 100
```

### How to redeploy the app for updates and fixes
```
git fetch origin
git reset --hard origin/main
git pull
pip install -r requirements.txt
sudo systemctl restart remindly
```

<img
class="statcounter"
src="https://c.statcounter.com/13168251/0/bb727728/1/"
alt="Web Analytics"
/>
