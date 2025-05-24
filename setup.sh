#!/bin/bash

# Virgil AI Setup Script
# This script sets up the complete environment on a fresh Ubuntu server

set -e  # Exit on error

echo "🚀 Starting Virgil AI Setup..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install basic dependencies
echo "🔧 Installing basic dependencies..."
apt install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    tmux

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "Docker Compose already installed"
fi

# Setup firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 3000/tcp
ufw --force enable

# Create project directory
echo "📁 Creating project structure..."
mkdir -p /opt/ai-code-generator
cd /opt/ai-code-generator

# Clone repository (you'll need to modify this with your actual repo)
echo "📥 Cloning repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/your-username/ai-code-generator.git .
else
    echo "Repository already exists, pulling latest changes..."
    git pull
fi

# Create necessary directories
mkdir -p output
mkdir -p logs

# Copy environment file
echo "🔐 Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys!"
    echo "Use: nano /opt/ai-code-generator/.env"
else
    echo ".env file already exists"
fi

# Setup NGINX
echo "🌐 Configuring NGINX..."
if [ -f "nginx.conf" ]; then
    cp nginx.conf /etc/nginx/sites-available/ai-code-generator
    ln -sf /etc/nginx/sites-available/ai-code-generator /etc/nginx/sites-enabled/
    
    # Disable default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test NGINX configuration
    nginx -t
    systemctl restart nginx
else
    echo "nginx.conf not found, skipping NGINX setup"
fi

# Create systemd service for the application
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/ai-code-generator.service << EOF
[Unit]
Description=Virgil AI
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10
WorkingDirectory=/opt/ai-code-generator
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
StandardOutput=append:/opt/ai-code-generator/logs/app.log
StandardError=append:/opt/ai-code-generator/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl daemon-reload
systemctl enable ai-code-generator.service

# Create helper scripts
echo "📝 Creating helper scripts..."

# Create update script
cat > /usr/local/bin/ai-codegen-update << 'EOFSCRIPT'
#!/bin/bash
cd /opt/ai-code-generator
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ Update complete!"
EOFSCRIPT
chmod +x /usr/local/bin/ai-codegen-update

# Create logs script
cat > /usr/local/bin/ai-codegen-logs << 'EOFSCRIPT'
#!/bin/bash
cd /opt/ai-code-generator
docker-compose logs -f $1
EOFSCRIPT
chmod +x /usr/local/bin/ai-codegen-logs

# Create status script
cat > /usr/local/bin/ai-codegen-status << 'EOFSCRIPT'
#!/bin/bash
cd /opt/ai-code-generator
docker-compose ps
EOFSCRIPT
chmod +x /usr/local/bin/ai-codegen-status

# Setup log rotation
echo "📋 Setting up log rotation..."
cat > /etc/logrotate.d/ai-code-generator << EOF
/opt/ai-code-generator/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload ai-code-generator
    endscript
}
EOF

# Create backup script
cat > /usr/local/bin/ai-codegen-backup << 'EOFSCRIPT'
#!/bin/bash
BACKUP_DIR="/backup/ai-code-generator"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
docker exec ai-code-generator-postgres-1 pg_dump -U codegenuser codegendb > $BACKUP_DIR/db_$DATE.sql

# Backup output directory
tar -czf $BACKUP_DIR/output_$DATE.tar.gz /opt/ai-code-generator/output/

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_DIR/*_$DATE.*"
EOFSCRIPT
chmod +x /usr/local/bin/ai-codegen-backup

# Add backup cron job
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/ai-codegen-backup") | crontab -

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Edit the .env file: nano /opt/ai-code-generator/.env"
echo "2. Start the application: systemctl start ai-code-generator"
echo "3. Check status: systemctl status ai-code-generator"
echo "4. View logs: ai-codegen-logs"
echo "5. Update domain in NGINX config: nano /etc/nginx/sites-available/ai-code-generator"
echo "6. Setup SSL: certbot --nginx -d your-domain.com"
echo ""
echo "📚 Helper commands:"
echo "- ai-codegen-status    : Check container status"
echo "- ai-codegen-logs      : View logs (use: ai-codegen-logs api)"
echo "- ai-codegen-update    : Update and restart application"
echo "- ai-codegen-backup    : Manual backup"
echo ""
echo "🌐 Access points:"
echo "- Frontend: http://your-server-ip:3000"
echo "- API: http://your-server-ip:8000"
echo "- API Docs: http://your-server-ip:8000/docs"