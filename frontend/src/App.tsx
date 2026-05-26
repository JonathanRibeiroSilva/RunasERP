import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoginPage from '@/pages/Login/LoginPage';
import RegisterPage from '@/pages/Register/RegisterPage';
import OAuthCallbackPage from '@/pages/Auth/OAuthCallbackPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import MainLayout from '@/components/layout/MainLayout/MainLayout';

// Loading component
const LoadingScreen = () => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: '#0F1115',
      color: '#E5E7EB',
    }}
  >
    <div className="text-center">
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Carregando...</span>
      </div>
      <p className="mt-3">Carregando...</p>
    </div>
  </div>
);

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  console.log('[ProtectedRoute] Estado:', { isAuthenticated, isLoading, user });

  if (isLoading) {
    console.log('[ProtectedRoute] Ainda carregando, mostrando LoadingScreen');
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Não autenticado, redirecionando para /login');
    return <Navigate to="/login" replace />;
  }

  console.log('[ProtectedRoute] Autenticado, renderizando children');
  return <>{children}</>;
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading, user } = useAuth();

  console.log('[PublicRoute] Estado:', { isAuthenticated, isLoading, user });

  if (isLoading) {
    console.log('[PublicRoute] Ainda carregando, mostrando LoadingScreen');
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    console.log('[PublicRoute] Autenticado, redirecionando para /dashboard');
    return <Navigate to="/dashboard" replace />;
  }

  console.log('[PublicRoute] Não autenticado, renderizando children (página pública)');
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />

        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />

        {/* OAuth Callback Route */}
        <Route path="/auth/callback" element={<OAuthCallbackPage />} />

        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<DashboardPage />} />
          {/* Outras rotas serão adicionadas aqui */}
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
