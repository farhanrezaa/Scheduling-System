# Educational Institute Scheduling System

A Streamlit web application for generating and managing class schedules for educational institutes.

## Features

- Generate schedules based on date ranges
- Edit schedules with an interactive data editor
- Download schedules as Excel files
- Support for multiple classes and subjects

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Locally

```bash
streamlit run scheduling_system.py
```

The app will open in your browser at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Cloud (Recommended - Easiest)

1. **Push to GitHub:**
   - Create a GitHub repository
   - Push your code (including `requirements.txt` and `scheduling_system.py`)

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository and branch
   - Set main file path: `scheduling_system.py`
   - Click "Deploy"

3. **Your app will be live** at `https://your-app-name.streamlit.app`

**Pros:** Free, automatic deployments, no server management
**Cons:** Public apps are free, private apps require paid plan

---

### Option 2: Docker Deployment

1. **Create a Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scheduling_system.py .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "scheduling_system.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Build and run:**
```bash
docker build -t scheduling-system .
docker run -p 8501:8501 scheduling-system
```

3. **Deploy to cloud:**
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances
   - DigitalOcean App Platform

---

### Option 3: Traditional Server Deployment

1. **On a Linux server (Ubuntu/Debian):**

```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Install systemd service (optional)
sudo nano /etc/systemd/system/scheduling-system.service
```

2. **Create systemd service file:**
```ini
[Unit]
Description=Streamlit Scheduling System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/scheduling_system
ExecStart=/usr/local/bin/streamlit run scheduling_system.py --server.port=8501 --server.address=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Enable and start:**
```bash
sudo systemctl enable scheduling-system
sudo systemctl start scheduling-system
```

4. **Set up reverse proxy (Nginx):**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

### Option 4: Cloud Platform Deployment

#### AWS (Elastic Beanstalk or EC2)
- Use Elastic Beanstalk with Python platform
- Or deploy on EC2 instance with systemd service

#### Google Cloud Platform
- Use Cloud Run (containerized)
- Or Compute Engine with systemd service

#### Azure
- Use Azure App Service (Python)
- Or Container Instances

#### Heroku
1. Create `Procfile`:
```
web: streamlit run scheduling_system.py --server.port=$PORT --server.address=0.0.0.0
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

---

## Environment Variables (Optional)

You can configure Streamlit using a `.streamlit/config.toml` file:

```toml
[server]
port = 8501
address = "0.0.0.0"

[browser]
gatherUsageStats = false
```

---

## Security Considerations

- For production, consider adding authentication
- Use HTTPS (SSL/TLS certificates)
- Set up firewall rules
- Consider using environment variables for sensitive data
- Add rate limiting if needed

---

## Troubleshooting

- **Port already in use:** Change the port in the command: `--server.port=8502`
- **Dependencies issues:** Ensure all packages in `requirements.txt` are installed
- **Excel export not working:** Verify `openpyxl` is installed

