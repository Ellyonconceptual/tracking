#!/usr/bin/env python3
"""
Setup script for Signal Bolt
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✓ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling Python dependencies...")
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\nCreating directories...")
    
    directories = [
        "logs",
        "data",
        "config",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")
    
    return True

def create_config_files():
    """Create configuration files"""
    print("\nCreating configuration files...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Signal Bolt Configuration
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=localhost
API_PORT=8000
WS_HOST=localhost
WS_PORT=8765

# Platform Configuration
IQ_OPTIONS_ENABLED=true
IQ_OPTIONS_API_KEY=
IQ_OPTIONS_USERNAME=
IQ_OPTIONS_PASSWORD=

# Signal Configuration
SIGNAL_EXPIRY_MINUTES=30
MAX_ACTIVE_SIGNALS=1000
CLEANUP_INTERVAL_SECONDS=60

# Database Configuration
DB_TYPE=sqlite
DATABASE_URL=sqlite:///signal_bolt.db

# Notifications
EMAIL_ENABLED=false
TELEGRAM_ENABLED=false
WEBHOOK_ENABLED=false
"""
        env_file.write_text(env_content)
        print("✓ Created .env file")
    else:
        print("✓ .env file already exists")
    
    return True

def create_startup_scripts():
    """Create startup scripts"""
    print("\nCreating startup scripts...")
    
    # Create start script for Linux/Mac
    start_script = """#!/bin/bash
# Signal Bolt Startup Script

echo "Starting Signal Bolt..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start Signal Bolt
echo "Starting Signal Bolt core..."
python3 signal_bolt.py &
SIGNAL_PID=$!

# Start API server
echo "Starting API server..."
python3 api.py &
API_PID=$!

echo "Signal Bolt started successfully!"
echo "Core PID: $SIGNAL_PID"
echo "API PID: $API_PID"
echo ""
echo "API available at: http://localhost:8000"
echo "WebSocket available at: ws://localhost:8765"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $SIGNAL_PID $API_PID; exit 0' INT
wait
"""
    
    Path("start.sh").write_text(start_script)
    os.chmod("start.sh", 0o755)
    print("✓ Created start.sh")
    
    # Create start script for Windows
    start_script_win = """@echo off
REM Signal Bolt Startup Script for Windows

echo Starting Signal Bolt...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\\Scripts\\activate.bat
)

REM Start Signal Bolt
echo Starting Signal Bolt core...
start /b python signal_bolt.py

REM Start API server
echo Starting API server...
start /b python api.py

echo Signal Bolt started successfully!
echo.
echo API available at: http://localhost:8000
echo WebSocket available at: ws://localhost:8765
echo.
echo Press any key to stop all services
pause >nul

REM Stop services
taskkill /f /im python.exe >nul 2>&1
echo Services stopped.
"""
    
    Path("start.bat").write_text(start_script_win)
    print("✓ Created start.bat")
    
    return True

def create_docker_files():
    """Create Docker configuration files"""
    print("\nCreating Docker files...")
    
    # Dockerfile
    dockerfile_content = """FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data config backups

# Expose ports
EXPOSE 8000 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "api.py"]
"""
    
    Path("Dockerfile").write_text(dockerfile_content)
    print("✓ Created Dockerfile")
    
    # docker-compose.yml
    compose_content = """version: '3.8'

services:
  signal-bolt:
    build: .
    ports:
      - "8000:8000"
      - "8765:8765"
    environment:
      - DEBUG=false
      - API_HOST=0.0.0.0
      - WS_HOST=0.0.0.0
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=signal_bolt
      - POSTGRES_USER=signal_bolt
      - POSTGRES_PASSWORD=signal_bolt
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
"""
    
    Path("docker-compose.yml").write_text(compose_content)
    print("✓ Created docker-compose.yml")
    
    return True

def run_tests():
    """Run basic tests"""
    print("\nRunning basic tests...")
    
    # Test imports
    try:
        import signal_bolt
        import client
        import api
        print("✓ All modules import successfully")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test basic functionality
    try:
        from signal_bolt import SignalBolt, TradingSignal, SignalType, SignalStrength
        from client import SignalBoltClient, SignalBoltConfig
        
        # Create a test signal
        signal = TradingSignal(
            id="test_123",
            symbol="EURUSD",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            timeframe=TimeFrame.M5,
            price=1.1000,
            timestamp=datetime.now(),
            expiry_time=datetime.now() + timedelta(minutes=30),
            confidence=0.8,
            platform="demo"
        )
        
        print("✓ Signal creation works")
        
        # Test client config
        config = SignalBoltConfig()
        print("✓ Client configuration works")
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False
    
    return True

def main():
    """Main setup function"""
    print("Signal Bolt Setup")
    print("================")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n✗ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n✗ Setup failed during directory creation")
        sys.exit(1)
    
    # Create config files
    if not create_config_files():
        print("\n✗ Setup failed during config file creation")
        sys.exit(1)
    
    # Create startup scripts
    if not create_startup_scripts():
        print("\n✗ Setup failed during startup script creation")
        sys.exit(1)
    
    # Create Docker files
    if not create_docker_files():
        print("\n✗ Setup failed during Docker file creation")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("\n✗ Setup failed during testing")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("✓ Signal Bolt setup completed successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Configure your .env file with your API keys")
    print("2. Run: python signal_bolt.py (in one terminal)")
    print("3. Run: python api.py (in another terminal)")
    print("4. Or use: ./start.sh (Linux/Mac) or start.bat (Windows)")
    print("\nFor Docker deployment:")
    print("1. Run: docker-compose up -d")
    print("\nAPI will be available at: http://localhost:8000")
    print("WebSocket will be available at: ws://localhost:8765")
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()