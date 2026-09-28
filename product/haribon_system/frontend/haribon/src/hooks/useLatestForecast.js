import { useCallback, useEffect, useState } from 'react';
import { useAppLocation } from '../context/LocationContext';
import ApiService from '../services/api';

const SLOW_LOAD_MS = 5000;

export default function useLatestForecast() {
  const [state, setState] = useState(() => {
    const cached = ApiService.getCachedForecast();
    return {
      data: cached?.data ?? null,
      stale: Boolean(cached),
      loading: true,
      error: null,
    };
  });
  const [slow, setSlow] = useState(false);
  const { selectedLocation, setSelectedLocation } = useAppLocation();

  const load = useCallback(async ({ force = false } = {}) => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await ApiService.getLatestForecast({ force });
      setState({ data, stale: false, loading: false, error: null });
    } catch (error) {
      setState((prev) => ({ ...prev, loading: false, error }));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Rebind the selected location to the newest payload so cached data never lingers in the UI.
  const { data } = state;
  useEffect(() => {
    if (!data?.locations?.length) return;
    const refreshed = selectedLocation?.id
      ? data.locations.find((loc) => loc.id === selectedLocation.id)
      : null;
    setSelectedLocation(refreshed || data.locations[0]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  useEffect(() => {
    if (!state.loading) {
      setSlow(false);
      return undefined;
    }
    const timer = setTimeout(() => setSlow(true), SLOW_LOAD_MS);
    return () => clearTimeout(timer);
  }, [state.loading]);

  const refresh = useCallback(() => load({ force: true }), [load]);

  return { ...state, slow, refresh };
}
