export interface GpsFix {
  latitude: number;
  longitude: number;
  accuracyMeters: number;
  timestamp: number;
}

export type GpsErrorCode =
  | "UNSUPPORTED"
  | "PERMISSION_DENIED"
  | "POSITION_UNAVAILABLE"
  | "TIMEOUT"
  | "UNKNOWN";

export class GpsLocationError extends Error {
  code: GpsErrorCode;

  constructor(code: GpsErrorCode, message: string) {
    super(message);
    this.name = "GpsLocationError";
    this.code = code;
  }
}

function mapGeolocationError(err: GeolocationPositionError): GpsLocationError {
  switch (err.code) {
    case err.PERMISSION_DENIED:
      return new GpsLocationError(
        "PERMISSION_DENIED",
        "Location permission was denied. Please enable browser location access or enter your village, taluk, district, and state manually."
      );
    case err.POSITION_UNAVAILABLE:
      return new GpsLocationError(
        "POSITION_UNAVAILABLE",
        "GPS position is currently unavailable on this device. Please retry outdoors or enter your farm location manually."
      );
    case err.TIMEOUT:
      return new GpsLocationError(
        "TIMEOUT",
        "GPS signal request timed out. Please retry or adjust the marker / fields manually."
      );
    default:
      return new GpsLocationError("UNKNOWN", "Unable to detect device GPS location.");
  }
}

/** Request exact current GPS coordinates from browser/device geolocation (no IP fallback, no hardcoded coordinates). */
export function requestCurrentGpsFix(): Promise<GpsFix> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      reject(
        new GpsLocationError(
          "UNSUPPORTED",
          "Geolocation is not supported in this browser. Please enter your farm location manually."
        )
      );
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          latitude: Number(position.coords.latitude.toFixed(6)),
          longitude: Number(position.coords.longitude.toFixed(6)),
          accuracyMeters: Math.round(position.coords.accuracy || 0),
          timestamp: position.timestamp,
        });
      },
      (err) => reject(mapGeolocationError(err)),
      {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 0,
      }
    );
  });
}

/** Start opt-in continuous GPS tracking; caller MUST expose an explicit stop control. */
export function startContinuousGpsWatch(
  onUpdate: (fix: GpsFix) => void,
  onError: (err: GpsLocationError) => void
): number {
  if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
    onError(
      new GpsLocationError(
        "UNSUPPORTED",
        "Continuous GPS tracking is unavailable in this browser."
      )
    );
    return -1;
  }

  return navigator.geolocation.watchPosition(
    (position) => {
      onUpdate({
        latitude: Number(position.coords.latitude.toFixed(6)),
        longitude: Number(position.coords.longitude.toFixed(6)),
        accuracyMeters: Math.round(position.coords.accuracy || 0),
        timestamp: position.timestamp,
      });
    },
    (err) => onError(mapGeolocationError(err)),
    {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 10000,
    }
  );
}

export function stopContinuousGpsWatch(watchId: number | null): void {
  if (watchId !== null && watchId >= 0 && typeof navigator !== "undefined" && "geolocation" in navigator) {
    navigator.geolocation.clearWatch(watchId);
  }
}
