#!/bin/bash

# Render build script for AI Employee Vault
# This script prepares the application for deployment on Render

set -e  # Exit on any error

echo "Starting build process for AI Employee Vault..."

# Install system dependencies that may be needed
apt-get update
apt-get install -y build-essential curl wget unzip xvfb libxi6 libgconf-2-4

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Chrome for Selenium (used in WhatsApp watcher)
echo "Installing Chrome for browser automation..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Set environment variables for headless browser operations
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
sleep 3

echo "Build process completed successfully!"
echo "AI Employee Vault is ready for deployment."