#!/bin/bash
# iOS Build Script for YT Downloader
# This script sets up the kivy-ios toolchain and builds the iOS app

set -e

echo "🍎 Setting up iOS build environment for YT Downloader..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: iOS builds require macOS"
    echo "Use GitHub Actions for automated builds on macOS runners"
    exit 1
fi

# Install dependencies via Homebrew
echo "📦 Installing build dependencies..."
brew install autoconf automake libtool pkg-config
brew link libtool

# Create and activate virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install kivy-ios and build tools
echo "🔧 Installing kivy-ios and build tools..."
pip install --upgrade pip
pip install kivy-ios cython

# Build the toolchain (this may take a while)
echo "🔨 Building kivy-ios toolchain (this may take 10-20 minutes)..."
toolchain build python3 kivy

# Stage the app files
echo "📁 Staging app files..."
mkdir -p ios_app
cp main.py ios_app/
cp requirements.txt ios_app/

# Create the Xcode project
echo "📱 Creating Xcode project..."
toolchain create YTDownloader ios_app

# Install Python dependencies
echo "📚 Installing Python dependencies..."
cd YTDownloader-ios
../toolchain pip install -r ../requirements.txt
cd ..

echo "✅ iOS build setup complete!"
echo "📱 Xcode project created in: YTDownloader-ios/"
echo ""
echo "Next steps:"
echo "1. Open the project: open YTDownloader-ios/YTDownloader.xcodeproj"
echo "2. Configure code signing in Xcode"
echo "3. Build and run on simulator or device"
