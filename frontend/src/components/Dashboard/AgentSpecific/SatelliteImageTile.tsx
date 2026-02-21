/**
 * SatelliteImageTile - Geography Agent satellite imagery display.
 * Shows satellite images from Microsoft Planetary Computer.
 */

import { useState, useEffect } from "react";
import { getSatelliteImageUrl } from "@/services/api";

interface SatelliteImageTileProps {
  imageReferences: string[];
  location: {
    name: string;
    coordinates: [number, number];
  };
  imageryDate: string;
  beforeDate?: string;
  ndviValues?: {
    min: number;
    max: number;
    mean: number;
  };
}

export function SatelliteImageTile({
  imageReferences,
  location,
  imageryDate,
  beforeDate,
  ndviValues,
}: SatelliteImageTileProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (imageReferences.length === 0) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    getSatelliteImageUrl(imageReferences[0])
      .then((url) => {
        setImageUrl(url);
        setIsLoading(false);
      })
      .catch((err) => {
        setError("Failed to load imagery");
        setIsLoading(false);
        console.error("Failed to fetch satellite image:", err);
      });
  }, [imageReferences]);

  return (
    <div className="satellite-image-tile">
      <div className="satellite-image-tile__header">Satellite Imagery</div>

      <div className="satellite-image-tile__image-container">
        {isLoading && (
          <div className="satellite-image-tile__loading">
            <div className="satellite-image-tile__spinner" />
            <span>Loading imagery...</span>
          </div>
        )}
        {error && (
          <div className="satellite-image-tile__error">
            <span>{error}</span>
          </div>
        )}
        {!isLoading && !error && imageUrl && (
          <img
            src={imageUrl}
            alt={`Satellite imagery of ${location.name}`}
            className="satellite-image-tile__image"
          />
        )}
        {!isLoading && !error && !imageUrl && (
          <div className="satellite-image-tile__placeholder">
            <svg
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <span>No imagery available</span>
          </div>
        )}
      </div>

      <div className="satellite-image-tile__caption">
        <div className="satellite-image-tile__location">
          <span className="satellite-image-tile__location-name">
            {location.name}
          </span>
          <span className="satellite-image-tile__coordinates">
            {location.coordinates[0].toFixed(4)},{" "}
            {location.coordinates[1].toFixed(4)}
          </span>
        </div>
        <div className="satellite-image-tile__dates">
          {beforeDate && <span className="satellite-image-tile__date">Before: {beforeDate}</span>}
          <span className="satellite-image-tile__date">
            {beforeDate ? "After: " : ""}{imageryDate}
          </span>
        </div>
        {ndviValues && (
          <div className="satellite-image-tile__ndvi">
            NDVI: {ndviValues.mean.toFixed(2)} (range: {ndviValues.min.toFixed(2)} - {ndviValues.max.toFixed(2)})
          </div>
        )}
      </div>
    </div>
  );
}
