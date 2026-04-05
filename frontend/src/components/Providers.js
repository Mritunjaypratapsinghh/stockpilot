'use client';
import { ToastProvider } from '../lib/toast';

export default function Providers({ children }) {
  return <ToastProvider>{children}</ToastProvider>;
}
