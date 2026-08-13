# iOS Code Signing Setup Guide

This guide explains how to set up code signing for iOS builds, both for local development and GitHub Actions.

## Local Development Setup

### 1. Apple Developer Account

You need an Apple Developer account to distribute iOS apps:
- **Individual**: $99/year for personal apps
- **Organization**: $99/year for company apps

### 2. Create Certificate and Provisioning Profile

#### Step 1: Create App ID
1. Go to [Apple Developer Portal](https://developer.apple.com/account)
2. Navigate to "Identifiers" → "App IDs"
3. Click "+" to create new App ID
4. Use Bundle ID: `org.mpagiwilliam.ytdownloader`
5. Enable capabilities needed (e.g., Photo Library access)

#### Step 2: Create Development Certificate
1. Go to "Certificates" → "Development"
2. Click "+" to create new certificate
3. Choose "iOS App Development"
4. Follow instructions to create CSR (Certificate Signing Request)
5. Download and install the certificate

#### Step 3: Create Provisioning Profile
1. Go to "Profiles" → "Development"
2. Click "+" to create new profile
3. Choose "iOS App Development"
4. Select your App ID
5. Select your development certificate
6. Select your test devices
7. Download the provisioning profile

### 3. Configure Xcode

1. Open the Xcode project: `open ios/YTDownloader-ios/YTDownloader.xcodeproj`
2. Select the project in the navigator
3. Go to "Signing & Capabilities" tab
4. Select your development team
5. Xcode will automatically manage signing

## GitHub Actions Setup

### 1. Export Certificate and Profile

#### Export Certificate (P12)
```bash
# Find your certificate in Keychain Access
# Right-click → Export → Save as .p12
# Set a password for the p12 file
```

#### Convert to Base64
```bash
# Convert certificate to base64
base64 -i certificate.p12 | pbcopy

# Convert provisioning profile to base64
base64 -i profile.mobileprovision | pbcopy
```

### 2. Add GitHub Secrets

Go to your repository settings → Secrets and variables → Actions

Add the following secrets:

#### For Debug Builds (Optional)
- `CERTIFICATE_BASE64`: Base64 encoded development certificate
- `CERTIFICATE_PASSWORD`: Password for the p12 file
- `PROVISIONING_PROFILE`: Base64 encoded provisioning profile

#### For Release Builds (Required for App Store)
- `CERTIFICATE_BASE64`: Base64 encoded distribution certificate
- `CERTIFICATE_PASSWORD`: Password for the p12 file
- `PROVISIONING_PROFILE`: Base64 encoded distribution provisioning profile
- `CODE_SIGN_IDENTITY`: Your signing identity (e.g., "iPhone Distribution: Your Name")
- `PROVISIONING_PROFILE_SPECIFIER`: Your profile name/UUID

### 3. Update Workflow

The workflow is already configured to use these secrets. For release builds, it will:
- Decode and install the certificate
- Install the provisioning profile
- Sign the app with your identity
- Create a distributable IPA

## Testing

### Local Testing
```bash
cd ios
./ios_build.sh
# Then open in Xcode and run on simulator/device
```

### GitHub Actions Testing
1. Push a tag to trigger a build: `git tag v1.0.0 && git push --tags`
2. Or manually trigger from Actions tab
3. Select build type (debug/release)
4. Download the IPA artifact
5. Test on device using TestFlight or direct installation

## Troubleshooting

### Common Issues

**Code signing errors**
- Verify certificate is valid and not expired
- Check provisioning profile matches App ID
- Ensure selected devices are included in profile

**Build failures**
- Check Xcode version compatibility
- Verify iOS deployment target settings
- Review build logs in GitHub Actions

**App crashes on device**
- Verify all required permissions are in Info.plist
- Check that file paths are correct for iOS sandboxing
- Test on multiple iOS versions

## Security Notes

- Never commit certificates or provisioning profiles to git
- Use GitHub Secrets for sensitive data
- Rotate certificates periodically
- Use separate certificates for development and production
- Limit certificate access to authorized team members