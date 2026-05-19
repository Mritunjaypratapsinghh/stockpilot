'use client';
import { Component, ReactNode } from 'react';

interface Props { children: ReactNode; fallbackMessage?: string; }
interface State { hasError: boolean; error: any; }

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }

  componentDidCatch(error: any, info: any) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[200px] p-6 text-center">
          <div className="w-12 h-12 mb-4 rounded-full bg-red-500/10 flex items-center justify-center">
            <span className="text-red-500 text-xl">!</span>
          </div>
          <h3 className="text-lg font-medium mb-2">Something went wrong</h3>
          <p className="text-[var(--text-muted)] text-sm mb-4">
            {this.props.fallbackMessage || 'This section failed to load.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 text-sm bg-[var(--accent)] text-white rounded-lg hover:bg-[#5558e3]"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
