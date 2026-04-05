'use client';
import { createContext, useContext, useState, useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';

const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const [state, setState] = useState(null);

  const confirm = useCallback((message = 'Are you sure?') => {
    return new Promise((resolve) => {
      setState({ message, resolve });
    });
  }, []);

  const handleClose = (result) => {
    state?.resolve(result);
    setState(null);
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => handleClose(false)}>
          <div className="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-lg p-6 w-full max-w-sm mx-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-[#ef4444]/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-[#ef4444]" />
              </div>
              <p className="text-[var(--text-primary)] font-medium">{state.message}</p>
            </div>
            <div className="flex gap-3">
              <button onClick={() => handleClose(false)} className="flex-1 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg text-sm">Cancel</button>
              <button onClick={() => handleClose(true)} className="flex-1 px-4 py-2 bg-[#ef4444] text-white rounded-lg text-sm">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export const useConfirm = () => useContext(ConfirmContext);
