import React, { useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import './QRScanner.css';

function QRScanner({ onScan }) {
  const qrCodeRef = useRef(null);
  const scannerRef = useRef(null);
  const [error, setError] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [cameras, setCameras] = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);

  useEffect(() => {
    // Get available cameras
    Html5Qrcode.getCameras()
      .then(devices => {
        if (devices && devices.length) {
          setCameras(devices);
          // Prefer back camera for mobile devices
          const backCamera = devices.find(device => 
            device.label.toLowerCase().includes('back') || 
            device.label.toLowerCase().includes('rear')
          );
          setSelectedCamera(backCamera ? backCamera.id : devices[0].id);
        } else {
          setError('No cameras found on this device');
        }
      })
      .catch(err => {
        console.error('Error getting cameras:', err);
        setError('Unable to access camera. Please check permissions.');
      });

    return () => {
      // Cleanup on unmount
      if (scannerRef.current && isScanning) {
        scannerRef.current.stop().catch(err => console.error('Error stopping scanner:', err));
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startScanning = () => {
    if (!selectedCamera) {
      setError('No camera selected');
      return;
    }

    const html5QrCode = new Html5Qrcode('qr-reader');
    scannerRef.current = html5QrCode;

    const config = {
      fps: 10,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0
    };

    html5QrCode.start(
      selectedCamera,
      config,
      (decodedText) => {
        // Successfully scanned
        console.log('QR Code decoded:', decodedText);
        
        // Stop scanning
        html5QrCode.stop()
          .then(() => {
            setIsScanning(false);
            onScan(decodedText);
          })
          .catch(err => console.error('Error stopping scanner:', err));
      },
      (errorMessage) => {
        // Scanning error (normal during scanning process)
        // console.log('Scan error:', errorMessage);
      }
    )
    .then(() => {
      setIsScanning(true);
      setError(null);
    })
    .catch(err => {
      console.error('Error starting scanner:', err);
      setError('Failed to start camera. Please check permissions and try again.');
    });
  };

  const stopScanning = () => {
    if (scannerRef.current && isScanning) {
      scannerRef.current.stop()
        .then(() => {
          setIsScanning(false);
        })
        .catch(err => console.error('Error stopping scanner:', err));
    }
  };

  return (
    <div className="qr-scanner-container">
      <div className="scanner-card">
        <h2>📷 Scan QR Code</h2>
        
        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}

        <div id="qr-reader" ref={qrCodeRef} className="qr-reader"></div>

        <div className="scanner-controls">
          {!isScanning ? (
            <button 
              className="btn btn-primary"
              onClick={startScanning}
              disabled={!selectedCamera}
            >
              Start Scanning
            </button>
          ) : (
            <button 
              className="btn btn-secondary"
              onClick={stopScanning}
            >
              Stop Scanning
            </button>
          )}
        </div>

        {cameras.length > 1 && !isScanning && (
          <div className="camera-selector">
            <label htmlFor="camera-select">Select Camera:</label>
            <select 
              id="camera-select"
              value={selectedCamera || ''}
              onChange={(e) => setSelectedCamera(e.target.value)}
            >
              {cameras.map(camera => (
                <option key={camera.id} value={camera.id}>
                  {camera.label || `Camera ${camera.id}`}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="scanner-instructions">
          <p>Position the QR code from your game card within the frame</p>
          <p className="note">Make sure to allow camera permissions when prompted</p>
        </div>
      </div>
    </div>
  );
}

export default QRScanner;
