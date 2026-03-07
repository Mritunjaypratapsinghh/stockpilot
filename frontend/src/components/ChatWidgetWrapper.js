'use client';
import { usePathname } from 'next/navigation';
import ChatWidget from './ChatWidget';

export default function ChatWidgetWrapper() {
  const pathname = usePathname();
  // Don't show on chat page (has full chat), login, or landing
  if (['/chat', '/login', '/landing'].includes(pathname)) return null;
  return <ChatWidget />;
}
