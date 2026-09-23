import { Component, ErrorInfo, ReactNode } from 'react';
import styles from './ErrorBoundary.module.css';

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
        <div className={styles.fallback}>
          <div className={styles.badge}>!</div>
          <h1 className={styles.title}>Ocurrió un problema</h1>
          <p className={styles.message}>
            Hubo un error inesperado al cargar la pantalla.
          </p>
          <button
            type="button"
            onClick={this.handleReset}
            className={styles.retry}
          >
            Recargar la página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
