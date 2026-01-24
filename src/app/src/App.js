import React, { useState } from 'react';
import './App.css';
import QRScanner from './components/QRScanner';
import PosterViewer from './components/PosterViewer';

function App() {
  const [posterUrl, setPosterUrl] = useState(null);
  const [scanning, setScanning] = useState(true);

  const handleQRCodeScanned = (url) => {
    console.log('QR Code scanned:', url);
    setPosterUrl(url);
    setScanning(false);
  };

  const handleBackToScanner = () => {
    setPosterUrl(null);
    setScanning(true);
  };

  return (
    <div className="App">
      {scanning && (
        <header className="App-header">
          <h1>🎬 Filmster</h1>
          <p>Movie Poster Guessing Game</p>
        </header>
      )}

      <main className="App-main">
        {scanning ? (
          <QRScanner onScan={handleQRCodeScanned} />
        ) : (
          <PosterViewer 
            posterUrl={posterUrl} 
            onBack={handleBackToScanner}
          />
        )}
      </main>

      {scanning && (
        <footer className="App-footer">
          <p>Scan a card's QR code to reveal the movie poster</p>
        </footer>
      )}
    </div>
  );
}

export default App;
