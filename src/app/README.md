# Filmster App

A Progressive Web App (PWA) for the Filmster movie poster guessing game.

## Features

- 📷 **QR Code Scanner** - Scan game cards using device camera
- 🎬 **Poster Viewer** - Display movie posters from GitHub Pages
- 📱 **Mobile-First** - Optimized for Android (Pixel 10 Pro and newer)
- 🚀 **PWA** - Installable as a native app on Android
- 🎨 **Beautiful UI** - Modern, responsive design

## Tech Stack

- **React** - UI framework
- **html5-qrcode** - QR code scanning library
- **Progressive Web App** - Installable on mobile devices

## Setup & Development

### Prerequisites

- Node.js (v16 or newer)
- npm or yarn

### Installation

1. Navigate to the app directory:
```bash
cd src/app
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

### Testing on Android

1. Make sure your phone and computer are on the same network
2. Find your computer's local IP address
3. Access the app from your phone: `http://YOUR_IP:3000`
4. Grant camera permissions when prompted

## Building for Production

1. Build the app:
```bash
npm run build
```

2. The optimized build will be in the `build/` folder

## Deployment to GitHub Pages

### Option 1: Manual Deployment

1. Build the app:
```bash
npm run build
```

2. Copy contents of `build/` folder to the root of your GitHub Pages repository

3. Make sure `game/posters/` directory is also in the repository

4. Push to GitHub

### Option 2: Automated with gh-pages

1. Install gh-pages:
```bash
npm install --save-dev gh-pages
```

2. Add to `package.json`:
```json
{
  "homepage": "https://YOUR_USERNAME.github.io/Filmster",
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d build"
  }
}
```

3. Deploy:
```bash
npm run deploy
```

## Installing on Android

### As a PWA (Recommended)

1. Open the app in Chrome on your Android device
2. Tap the menu (⋮) → "Add to Home screen" or "Install app"
3. The app will be installed like a native app
4. Launch from your home screen

### Features of PWA Install:
- ✓ Full screen mode
- ✓ App icon on home screen
- ✓ Splash screen
- ✓ Works like native app
- ✓ No app store needed

## Camera Permissions

The app requires camera access to scan QR codes. When prompted:

1. Allow camera permissions
2. If denied, go to:
   - **Chrome:** Settings → Site Settings → Camera → Allow
   - **Android Settings:** Apps → Chrome → Permissions → Camera → Allow

## Future Features (Not Yet Implemented)

- 🎵 Spotify integration
- 🏆 Scoring system
- ⏱️ Timer
- 👥 Multiplayer mode
- 📊 Statistics

## Troubleshooting

### Camera not working
- Check browser permissions
- Try using Chrome (recommended)
- Make sure you're using HTTPS or localhost

### QR code not scanning
- Ensure good lighting
- Hold card steady and parallel to camera
- Try moving closer/farther from card

### Poster not loading
- Check GitHub Pages URL is correct
- Verify poster exists in `game/posters/` directory
- Check console for error messages

## Project Structure

```
src/app/
├── public/
│   ├── index.html          # HTML template
│   ├── manifest.json       # PWA manifest
│   └── favicon.ico         # App icon
├── src/
│   ├── components/
│   │   ├── QRScanner.js    # QR scanning component
│   │   ├── QRScanner.css
│   │   ├── PosterViewer.js # Poster display component
│   │   └── PosterViewer.css
│   ├── App.js              # Main app component
│   ├── App.css
│   ├── index.js            # Entry point
│   └── index.css
├── package.json
└── README.md
```

## Development Notes

- The app is designed mobile-first
- Uses camera selector for devices with multiple cameras
- Automatically prefers back camera on mobile
- Responsive design works on tablets and desktop too
- Ready for future Spotify API integration

## License

MIT
