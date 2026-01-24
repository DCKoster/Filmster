import React, { useState } from 'react';
import './PosterViewer.css';

function PosterViewer({ posterUrl, onBack }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
  };

  const handleImageError = () => {
    setImageLoaded(false);
    setImageError(true);
  };

  return (
    <div className="poster-viewer-container">
      {!imageLoaded && !imageError && (
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading poster...</p>
        </div>
      )}

      {imageError && (
        <div className="error-message">
          <p>⚠️ Failed to load poster</p>
          <p className="error-detail">URL: {posterUrl}</p>
        </div>
      )}

      <div className={`poster-wrapper-fullscreen ${imageLoaded ? 'loaded' : ''}`}>
        <img
          src={posterUrl}
          alt="Movie Poster"
          className="poster-image-fullscreen"
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      </div>

      <div className="viewer-controls-bottom">
        <button 
          className="btn btn-back-simple"
          onClick={onBack}
        >
          Scan Another Card
        </button>
      </div>
    </div>
  );
}

export default PosterViewer;
