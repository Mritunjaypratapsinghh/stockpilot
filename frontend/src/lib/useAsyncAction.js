import { useState, useCallback } from 'react';
import { useToast } from './toast';

export function useAsyncAction(asyncFn, { onSuccess, successMsg, errorMsg } = {}) {
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const execute = useCallback(async (...args) => {
    if (loading) return;
    setLoading(true);
    try {
      const result = await asyncFn(...args);
      if (successMsg) toast?.success(successMsg);
      onSuccess?.(result);
      return result;
    } catch (e) {
      toast?.error(errorMsg || e.message || 'Something went wrong');
      throw e;
    } finally {
      setLoading(false);
    }
  }, [asyncFn, loading, onSuccess, successMsg, errorMsg, toast]);

  return [execute, loading];
}
