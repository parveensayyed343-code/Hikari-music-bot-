#!/usr/bin/env bash
# build.sh — runs on Render during build phase

set -e

echo "📦 Installing system dependencies..."
apt-get update -y
apt-get install -y \
    ffmpeg \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Build complete!"
