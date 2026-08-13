# SideStore Distribution Guide

## What is SideStore?

SideStore is an open-source alternative to AltStore for sideloading iOS apps without an Apple Developer account. It's community-driven and free to use.

## ✅ Yes, You Can Distribute via SideStore

You can absolutely distribute your finished app through SideStore! Here's how:

## Distribution Methods

### Method 1: Direct IPA Download (Recommended)

1. **Host Your IPA**:
   - Upload your IPA to your website
   - Create a download page with installation instructions

2. **User Installation Process**:
   - Users install SideStore on their iOS device
   - Users download your IPA from your website
   - Users open SideStore and select your IPA file
   - SideStore installs the app on their device

### Method 2: SideStore Source (Advanced)

SideStore supports "sources" - repositories of apps. You can create your own source:

1. **Create a SideStore Source**:
   - Host a JSON file with app metadata
   - Include your IPA download URL
   - Users add your source to SideStore
   - Your app appears in their SideStore browse section

### Method 3: Community Repositories

You can submit your app to existing SideStore community repositories:
- SideStore's official community sources
- Third-party app directories

## User Installation Instructions

### For Your Website Users

**Step 1: Install SideStore**
1. Download SideStore from [https://sidestore.io](https://sidestore.io)
2. Follow the installation guide on their website
3. Requires a computer (Mac/Windows) for initial setup

**Step 2: Download Your App**
1. Visit your website
2. Download the YTDownloader IPA file
3. Open SideStore on your iOS device

**Step 3: Install the App**
1. In SideStore, tap the "+" button
2. Select your downloaded IPA file
3. Enter your Apple ID (for signing)
4. Wait for installation to complete
5. Find YTDownloader on your home screen

## App Refresh Requirements

### Important: 7-Day Expiration

Like all sideloaded apps, your app will expire after 7 days. Users need to:

1. **Refresh Before Expiration**:
   - Open SideStore
   - Find YTDownloader in the app list
   - Tap "Refresh" button
   - Enter Apple ID password
   - App is valid for another 7 days

2. **Automated Refresh**:
   - SideStore can refresh apps automatically in the background
   - Users need to enable this in SideStore settings
   - Requires SideStore to be running periodically

## Your Website Integration

### Download Page Template

```html
<h1>Download YTDownloader for iOS</h1>

<div class="download-section">
  <h2>Installation Instructions</h2>
  
  <ol>
    <li>Install SideStore from <a href="https://sidestore.io">sidestore.io</a></li>
    <li>Download the IPA file below</li>
    <li>Open SideStore on your iOS device</li>
    <li>Tap the "+" button and select the IPA file</li>
    <li>Enter your Apple ID when prompted</li>
    <li>Wait for installation to complete</li>
  </ol>
  
  <a href="downloads/YTDownloader-latest.ipa" class="download-btn">
    Download YTDownloader IPA
  </a>
  
  <p class="warning">
    ⚠️ Note: This app expires after 7 days. Refresh it using SideStore 
    before expiration to continue using it.
  </p>
</div>
```

### Version Management

1. **Update Your Website**:
   - Upload new IPA builds to your website
   - Update the download link to point to the latest version
   - Keep old versions available if needed

2. **Version Information**:
   - Display current version number
   - Show release notes
   - Provide download links for previous versions

## Benefits of SideStore Distribution

### Advantages
- **Free**: No Apple Developer account needed
- **Open Source**: Community-driven development
- **No Revokes**: More stable than some alternatives
- **Cross-Platform**: Works with Mac, Windows, and Linux
- **Custom Sources**: You can create your own app repository

### Limitations
- **7-Day Expiration**: Apps need refreshing weekly
- **Initial Setup**: Requires computer for first-time SideStore installation
- **Apple ID Required**: Users need personal Apple ID for signing
- **Device Limit**: 3 apps per device (free Apple ID)

## Comparison with Other Methods

| Method | Cost | Expiration | Difficulty | Your Control |
|--------|------|------------|------------|--------------|
| **SideStore** | Free | 7 days | Medium | High |
| **AltStore** | Free | 7 days | Medium | High |
| **Sideloadly** | Free | 7 days | Easy | High |
| **App Store** | $99/year | Never | Hard | Medium |
| **Enterprise** | $299/year | 1 year | Hard | Low |

## Security Considerations

### For Your Users
- Only download from your official website
- Verify the IPA file integrity (provide checksums)
- Warn against downloading from unofficial sources

### For Your App
- Your IPA is unsigned - normal for sideloading
- Users sign with their own Apple ID
- No security risk to your Apple Developer account (you don't need one)

## Technical Requirements

### Your Website
- **Hosting**: Any web hosting service
- **Bandwidth**: IPA files are typically 50-200MB
- **SSL**: HTTPS is recommended for secure downloads
- **Storage**: Space for multiple app versions

### IPA File
- **Format**: Standard iOS App Store Package (.ipa)
- **Signing**: Unsigned (for sideloading)
- **Size**: Optimize to reduce download time

## Advanced: Create Your Own SideStore Source

If you want to go beyond simple downloads, you can create a SideStore source:

### Source JSON Structure
```json
{
  "name": "YTDownloader Source",
  "identifier": "com.ytdownloader.source",
  "apps": [
    {
      "name": "YTDownloader",
      "bundleIdentifier": "org.mpagiwilliam.ytdownloader",
      "version": "2.0.0",
      "versionDate": "2026-08-13",
      "downloadURL": "https://yourwebsite.com/downloads/YTDownloader-2.0.0.ipa",
      "localizedDescription": "Download YouTube videos and audio",
      "iconURL": "https://yourwebsite.com/icon.png",
      "developerName": "Mpagi William",
      "size": 15000000
    }
  ]
}
```

### Hosting Your Source
1. Host the JSON file on your website
2. Users add your source URL in SideStore
3. Your app appears in their SideStore browse section
4. Updates are automatic when you update the JSON

## Next Steps

1. **Build Your App**: Use GitHub Actions to create the IPA
2. **Host the IPA**: Upload to your website
3. **Create Download Page**: Add installation instructions
4. **Test the Process**: Try installing from your website
5. **Launch**: Share the download link with users

## Support Resources

- **SideStore Website**: [https://sidestore.io](https://sidestore.io)
- **SideStore GitHub**: [https://github.com/SideStore/SideStore](https://github.com/SideStore/SideStore)
- **Documentation**: Available on their website
- **Community**: Discord and Reddit communities available

## Legal Considerations

- YouTube downloading may violate YouTube's Terms of Service
- Ensure your app complies with copyright laws in your jurisdiction
- Consider adding disclaimers to your website
- Be prepared for potential app functionality changes due to YouTube updates

---

This approach gives you full control over distribution while avoiding Apple Developer account requirements and App Store review processes.