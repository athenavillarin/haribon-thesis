import { useCallback, useEffect, useState } from 'react';
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
