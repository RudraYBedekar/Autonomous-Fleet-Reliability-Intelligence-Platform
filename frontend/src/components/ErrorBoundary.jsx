import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('[Fleet UI]', error, info?.componentStack);
  }

  render() {
    const { error } = this.state;
    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full w-full bg-dark-900 text-gray-200 p-6 text-center gap-3">
          <p className="text-red-400 font-semibold">Something went wrong displaying the map.</p>
          <p className="text-xs text-gray-500 max-w-md">{error.message}</p>
          <button
            type="button"
            onClick={() => this.setState({ error: null })}
            className="px-4 py-2 text-sm rounded-lg bg-brand-blue text-white"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
