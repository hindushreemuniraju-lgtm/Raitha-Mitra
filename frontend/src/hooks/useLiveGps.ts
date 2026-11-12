import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/services/api";
import {
  GpsFix,
  GpsLocationError,
  requestCurrentGpsFix,
  startContinuousGpsWatch,
  stopContinuousGpsWatch,
} from "@/services/gpsService";
import type { ReverseGeocodeResult } from "@/types";

export interface DetectedLocationPayload extends GpsFix {
  geocoded?: ReverseGeocodeResult | null;
}

export function useLiveGps(options?: {
  initialContinuous?: boolean;
  onDetected?: (payload: DetectedLocationPayload) => void;
}) {
  const [detecting, setDetecting] = useState(false);
  const [watching, setWatching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFix, setLastFix] = useState<GpsFix | null>(null);
  const [geocoded, setGeocoded] = useState<ReverseGeocodeResult | null>(null);
  const watchIdRef = useRef<number | null>(null);
  const onDetectedRef = useRef(options?.onDetected);
  onDetectedRef.current = options?.onDetected;

  const reverseLookup = useCallback(async (lat: number, lon: number, allowAuthFetch = true) => {
    if (allowAuthFetch) {
      try {
        const res = await api.reverseGeocode(lat, lon);
        setGeocoded(res);
        return res;
      } catch {
        // Fallback for unauthenticated registration page using public Nominatim direct lookup
      }
    }
    try {
      const resp = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json&addressdetails=1`,
        { headers: { "Accept-Language": "en" } }
      );
      if (resp.ok) {
        const data = await resp.json();
        const addr = data?.address || {};
        const village = String(
          addr.village || addr.hamlet || addr.suburb || addr.neighbourhood || addr.town || addr.city || ""
        ).trim();
        const taluk = String(
          addr.county || addr.subdistrict || addr.municipality || addr.town || ""
        )
          .replace(/\s+taluk(a)?$/i, "")
          .trim();
        const district = String(
          addr.state_district || addr.county || addr.city_district || addr.city || ""
        )
          .replace(/\s+district$/i, "")
          .trim();
        const state = String(addr.state || "").trim();
        const res: ReverseGeocodeResult = {
          status: "ok",
          latitude: lat,
          longitude: lon,
          village,
          taluk,
          district,
          state,
          display_name: String(data?.display_name || [village, taluk, district, state].filter(Boolean).join(", ")),
          source: "OpenStreetMap Nominatim",
        };
        setGeocoded(res);
        return res;
      }
    } catch {
      // Ignore reverse lookup errors gracefully; manual editing remains available
    }
    return null;
  }, []);

  const detectOnce = useCallback(
    async (allowAuthReverse = true) => {
      setDetecting(true);
      setError(null);
      try {
        const fix = await requestCurrentGpsFix();
        setLastFix(fix);
        const geo = await reverseLookup(fix.latitude, fix.longitude, allowAuthReverse);
        onDetectedRef.current?.({ ...fix, geocoded: geo });
        return { ...fix, geocoded: geo };
      } catch (err) {
        const msg =
          err instanceof GpsLocationError || err instanceof Error
            ? err.message
            : "Could not detect GPS location.";
        setError(msg);
        return null;
      } finally {
        setDetecting(false);
      }
    },
    [reverseLookup]
  );

  const stopWatching = useCallback(() => {
    stopContinuousGpsWatch(watchIdRef.current);
    watchIdRef.current = null;
    setWatching(false);
  }, []);

  const startWatching = useCallback(
    (allowAuthReverse = true) => {
      stopWatching();
      setError(null);
      const id = startContinuousGpsWatch(
        async (fix) => {
          setLastFix(fix);
          const geo = await reverseLookup(fix.latitude, fix.longitude, allowAuthReverse);
          onDetectedRef.current?.({ ...fix, geocoded: geo });
        },
        (err) => {
          setError(err.message);
          stopWatching();
        }
      );
      if (id >= 0) {
        watchIdRef.current = id;
        setWatching(true);
      }
    },
    [reverseLookup, stopWatching]
  );

  useEffect(() => {
    if (options?.initialContinuous) {
      startWatching(true);
    }
    return () => stopContinuousGpsWatch(watchIdRef.current);
  }, [options?.initialContinuous, startWatching]);

  return {
    detecting,
    watching,
    error,
    lastFix,
    geocoded,
    detectOnce,
    reverseLookup,
    startWatching,
    stopWatching,
    clearError: () => setError(null),
  };
}
