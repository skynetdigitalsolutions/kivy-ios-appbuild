# YT Downloader iOS Build

iOS version of the YT Downloader application built with Kivy and kivy-ios for distribution via sideloading.

## Project Structure

```
IOS-build/
├── ios/                      # iOS-specific source code
│   ├── main.py              # Main application code
│   ├── requirements.txt     # Python dependencies
│   ├── Info.plist          # iOS app configuration
│   ├── toolchain.py        # Custom kivy-ios toolchain config
│   ├── ios_build.sh        # Local build script
│   ├── SIDELOADING_GUIDE.md # User installation guide
│   ├── codesign-setup.md    # Code signing documentation
│   └── .github/
│       └── workflows/
│           └── ios-build.yml # GitHub Actions workflow
└── README.md               # This file
```

## Features

- **Cross-platform**: Built with Kivy for iOS compatibility
- **Sideloading Support**: Unsigned IPA for AltStore/SideStore/Sideloadly
- **Automated Builds**: GitHub Actions CI/CD pipeline
- **No Apple Developer Account Required**: For personal use distribution
- **YouTube Downloading**: Download videos and audio using yt-dlp

## Quick Start

### GitHub Actions Setup

1. **Initialize Git Repository** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub Repository**:
   - Go to GitHub and create a new repository
   - Follow the instructions to connect your local repository

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/yourusername/your-repo.git
   git branch -M main
   git push -u origin main
   ```

4. **Enable GitHub Actions**:
   - Go to your repository on GitHub
   - Navigate to Settings → Actions → General
   - Enable "Allow all actions and reusable workflows"

5. **Trigger Build**:
   - Push a tag: `git tag v1.0.0 && git push --tags`
   - Or manually trigger from Actions tab

6. **Download IPA**:
   - Wait for build to complete (~15-20 minutes)
   - Download the unsigned IPA from artifacts
   - Upload to your website for distribution

## GitHub Actions Workflow

The workflow is configured to:
- Run on macOS-14 runner
- Install Python 3.11 and build tools
- Build kivy-ios toolchain
- Create Xcode project
- Build unsigned IPA for sideloading
- Upload artifacts with 90-day retention

### Workflow Triggers

- Manual trigger (with version input)
- Tag pushes (v*)
- Main branch pushes
- Pull requests to main

## Requirements

### For Building
- GitHub repository with Actions enabled
- No Apple Developer account required (for unsigned builds)

### For Users (Sideloading)
- iOS device with iOS 13.0+
- Sideloading tool (AltStore, SideStore, or Sideloadly)
- Personal Apple ID

## Documentation

- [iOS Build Guide](ios/README.md) - Detailed iOS build instructions
- [Sideloading Guide](ios/SIDELOADING_GUIDE.md) - User installation instructions
- [Code Signing Setup](ios/codesign-setup.md) - For signed builds (optional)

## Developers

- **Mpagi William** - Full-Stack Developer
- **Tong Bbosa** - Full-Stack Developer

**Contact**: skynetdigitalsolutionsug@gmail.com

## License

See main project license for details.