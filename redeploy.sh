#!/bin/bash

# Get the latest code
git fetch origin
git reset --hard origin/main
git pull

# Install requirements if "install" parameter is passed
if [ "$1" == "install" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing requirements"
        exit 1
    fi
fi

# Restart the service
echo "Restarting service..."
sudo systemctl restart remindly
if [ $? -ne 0 ]; then
    echo "Error restarting service"
    exit 1
fi