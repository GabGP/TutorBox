import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Root Error Boundary for the TutorBox application.
 * Catches rendering exceptions and displays a fallback recovery screen
 * instead of a blank page.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  /**
   * Catches errors thrown by children and logs diagnostic stack trace.
   *
   * @param {Error} error - The error thrown by descendant component.
   * @param {ErrorInfo} errorInfo - Component stack trace information.
   * @returns {void}
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('TutorBox Uncaught Error:', error, errorInfo);
  }

  /**
   * Clears error boundary state and reloads the active browser page.
   *
   * @returns {void}
   */
  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            padding: '20px',
            textAlign: 'center',
            fontFamily: 'system-ui, -apple-system, sans-serif',
            background: 'var(--panel, #f7fbfd)',
            color: 'var(--ink, #131e23)',
          }}
        >
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '20px',
              background: 'var(--bad, #b3261e)',
              color: '#fff',
              display: 'grid',
              placeItems: 'center',
              fontSize: '32px',
              fontWeight: 700,
              marginBottom: '16px',
            }}
          >
            !
          </div>
          <h1 style={{ fontSize: '24px', margin: '0 0 8px' }}>Ocurrió un problema</h1>
          <p style={{ color: 'var(--mute, #576b74)', margin: '0 0 24px', maxWidth: '400px' }}>
            Hubo un error inesperado al cargar la pantalla.
          </p>
          <button
            type="button"
            onClick={this.handleReset}
            style={{
              height: '48px',
              padding: '0 24px',
              borderRadius: '24px',
              background: 'var(--p, #0b6e99)',
              color: '#fff',
              fontSize: '16px',
              fontWeight: 600,
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Recargar la página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
