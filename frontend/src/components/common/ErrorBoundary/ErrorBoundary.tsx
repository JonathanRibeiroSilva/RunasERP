import { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Contém crashes de renderização: ao invés de desmontar toda a árvore React
 * para uma tela em branco, exibe um fallback recuperável.
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Reporte estruturado (Sentry) entra no item M4; por ora, visibilidade do crash.
    console.error('ErrorBoundary caught a render error:', error, info.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false });
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          padding: '2rem',
          textAlign: 'center',
          color: '#E5E7EB',
        }}
      >
        <h2 style={{ marginBottom: '0.5rem' }}>Algo deu errado</h2>
        <p style={{ marginBottom: '1.5rem', color: '#9CA3AF' }}>
          Ocorreu um erro inesperado nesta página. Você pode tentar novamente.
        </p>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-primary" onClick={this.handleReset}>
            Tentar novamente
          </button>
          <button className="btn btn-outline-secondary" onClick={() => window.location.reload()}>
            Recarregar página
          </button>
        </div>
      </div>
    );
  }
}

export default ErrorBoundary;
