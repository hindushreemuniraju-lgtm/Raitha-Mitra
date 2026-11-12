import { useCallback, useState } from "react";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  run: (fn: () => Promise<T>) => Promise<T | null>;
  setData: React.Dispatch<React.SetStateAction<T | null>>;
  resetError: () => void;
}

export function useAsyncState<T>(initialData: T | null = null): AsyncState<T> {
  const [data, setData] = useState<T | null>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (fn: () => Promise<T>) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      setData(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unexpected error occurred.";
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const resetError = useCallback(() => setError(null), []);

  return { data, loading, error, run, setData, resetError };
}
