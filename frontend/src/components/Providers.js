'use client';
import { ToastProvider } from '../lib/toast';
import { ConfirmProvider } from '../lib/confirm';

export default function Providers({ children }) {
  return (
    <ToastProvider>
      <ConfirmProvider>{children}</ConfirmProvider>
    </ToastProvider>
  );
}
