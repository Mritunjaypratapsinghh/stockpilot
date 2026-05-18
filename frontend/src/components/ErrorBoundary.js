'use client';
import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
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
