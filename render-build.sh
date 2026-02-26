#!/usr/bin/env bash

echo "Installing Chrome & dependencies..."

sudo apt-get update
sudo apt-get install -y wget unzip fontconfig libfontconfig1 libjpeg-turbo8 libpng16-16 libx11-6 libxcb1 libxext6 libxrender1 xfonts-75dpi xfonts-base libgtk-3-0 libnss3 libgconf-2-4 libasound2 libdbus-glib-1-2 libxt6

# Install latest stable Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

echo "Chrome installed. Version:"
google-chrome --version

# Optional: Install Chromium as fallback
sudo apt-get install -y chromium-browser

# Your normal pip install
pip install -r requirements.txt