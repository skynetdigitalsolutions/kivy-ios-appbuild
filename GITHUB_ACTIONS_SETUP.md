# GitHub Actions Setup Guide

This guide will help you set up GitHub Actions for automated iOS builds of the YT Downloader app.

## Prerequisites

- GitHub account
- Local git repository (already initialized)
- Project files committed to git

## Step 1: Create GitHub Repository

1. **Go to GitHub**:
   - Navigate to [https://github.com](https://github.com)
   - Click the "+" icon in the top-right corner
   - Select "New repository"

2. **Configure Repository**:
   - Repository name: `YTDownloader-iOS` (or your preferred name)
   - Description: `iOS YT Downloader built with Kivy and GitHub Actions`
   - Visibility: Choose Public or Private
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)

3. **Create Repository**:
   - Click "Create repository"

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you instructions. Follow these steps:

1. **Add Remote URL**:
   ```bash
   cd "C:\Users\HP\Desktop\IOS-build"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   ```
   Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual values.

2. **Rename Branch to Main** (if needed):
   ```bash
   git branch -M main
   ```

3. **Push to GitHub**:
   ```bash
   git push -u origin main
   ```

   You'll be prompted for your GitHub username and password (or personal access token).

## Step 3: Enable GitHub Actions

1. **Go to Repository Settings**:
   - Navigate to your repository on GitHub
   - Click "Settings" tab

2. **Enable Actions**:
   - Click "Actions" in the left sidebar
   - Click "General" under Actions
   - Scroll to "Actions permissions"
   - Select "Allow all actions and reusable workflows"
   - Click "Save"

## Step 4: Verify Workflow Configuration

Your GitHub Actions workflow is already configured in `.github/workflows/ios-build.yml`. It includes:

- **Build Environment**: macOS-14 runner
- **Python Setup**: Python 3.11
- **Build Tools**: Homebrew, kivy-ios, cython
- **Caching**: Toolchain caching for faster builds
- **Build Process**: Toolchain build, Xcode project creation, IPA packaging
- **Artifacts**: Unsigned IPA with 90-day retention

## Step 5: Configure GitHub Secrets (Optional)

For **unsigned builds** (current configuration), no secrets are required. The workflow builds IPAs for sideloading without code signing.

### Optional: Code Signing for App Store Distribution

If you want to distribute via App Store in the future, you'll need to add these secrets in GitHub:

1. **Go to Repository Settings**:
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"

2. **Add Secrets**:
   - `CERTIFICATE_BASE64`: Base64 encoded development/distribution certificate
   - `CERTIFICATE_PASSWORD`: Password for the p12 file
   - `PROVISIONING_PROFILE`: Base64 encoded provisioning profile
   - `CODE_SIGN_IDENTITY`: Your signing identity
   - `PROVISIONING_PROFILE_SPECIFIER`: Your profile name/UUID

See `ios/codesign-setup.md` for detailed code signing instructions.

## Step 6: Trigger Your First Build

### Option A: Manual Trigger (Recommended for First Build)

1. **Go to Actions Tab**:
   - Navigate to your repository on GitHub
   - Click "Actions" tab

2. **Select Workflow**:
   - You should see "Build iOS App (Unsigned for Sideloading)"
   - Click "Run workflow"

3. **Enter Version**:
   - Enter version number (e.g., "2.0.0")
   - Click "Run workflow"

### Option B: Tag-Based Trigger

```bash
git tag v2.0.0
git push --tags
```

### Option C: Push to Main Branch

```bash
# Make any change to a file
git add .
git commit -m "Test trigger"
git push origin main
```

## Step 7: Monitor Build Progress

1. **Watch Build Progress**:
   - Go to Actions tab
   - Click on the running workflow
   - You can see real-time logs

2. **Expected Build Time**:
   - First build: 15-20 minutes (toolchain compilation)
   - Subsequent builds: 5-10 minutes (due to caching)

## Step 8: Download Build Artifacts

1. **After Build Completes**:
   - Go to Actions tab
   - Click on the completed workflow run
   - Scroll to "Artifacts" section at the bottom

2. **Download IPA**:
   - Find `YTDownloader-iOS-unsigned-{build_number}`
   - Click to download the ZIP file
   - Extract to get the `.ipa` file

3. **IPA Naming**:
   - Format: `YTDownloader-{version}-{build_number}-unsigned.ipa`
   - Example: `YTDownloader-2.0.0-1-unsigned.ipa`

## Step 9: Deploy for Distribution

1. **Upload to Your Website**:
   - Upload the IPA file to your web server
   - Create a download page for users

2. **Alternative Distribution**:
   - Use file sharing services (Google Drive, Dropbox, etc.)
   - Share direct download links with users

## Step 10: User Installation

Users can install the IPA using:
- **AltStore** (recommended for iOS)
- **SideStore** (open-source alternative)
- **Sideloadly** (for Windows/Linux)

See `ios/SIDELOADING_GUIDE.md` for detailed user instructions.

## Troubleshooting

### Build Fails

1. **Check Logs**:
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages in logs

2. **Common Issues**:
   - Python version mismatch
   - Missing dependencies in requirements.txt
   - Kivy-ios toolchain errors
   - Xcode build configuration issues

### Workflow Doesn't Appear

1. **Verify File Location**:
   - Ensure `.github/workflows/ios-build.yml` exists
   - Check file is committed to repository

2. **Check Actions Permissions**:
   - Settings → Actions → General
   - Ensure actions are enabled

### Push Fails

1. **Authentication Issues**:
   - Use GitHub personal access token instead of password
   - Ensure token has `repo` scope

2. **Branch Protection**:
   - If main branch is protected, adjust settings or use different branch

## Workflow Features

### Triggers
- Manual trigger with version input
- Tag pushes (v*)
- Main branch pushes
- Pull requests to main

### Caching
- Toolchain caching for faster builds
- Cache key based on requirements.txt

### Artifacts
- Unsigned IPA files
- 90-day retention
- Build logs on failure (7-day retention)

### Concurrency
- Cancels in-progress builds for same branch
- Prevents resource conflicts

## Next Steps

1. **Test First Build**: Trigger a manual build to verify setup
2. **Download IPA**: Test the artifact download process
3. **Sideloading Test**: Install IPA on a test device
4. **Update Documentation**: Customize guides for your specific needs
5. **Set Up Releases**: Consider using GitHub Releases for version management

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kivy iOS Documentation](https://github.com/kivy/kivy-ios)
- [iOS Sideloading Guide](ios/SIDELOADING_GUIDE.md)
- [Code Signing Setup](ios/codesign-setup.md)

## Support

For issues or questions:
- Email: skynetdigitalsolutionsug@gmail.com
- Developers: Mpagi William, Tong Bbosa