import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoginPage from '@/pages/Login/LoginPage';
import RegisterPage from '@/pages/Register/RegisterPage';
import OAuthCallbackPage from '@/pages/Auth/OAuthCallbackPage';
import GoogleCallback from '@/pages/Auth/GoogleCallback';
import MicrosoftCallback from '@/pages/Auth/MicrosoftCallback';
import ForgotPasswordPage from '@/pages/Auth/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/Auth/ResetPasswordPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import PerfilPage from '@/pages/Perfil/PerfilPage';
import ClientesPage from '@/pages/Clientes/ClientesPage';
import ClienteFormPage from '@/pages/Clientes/ClienteFormPage';
import ClienteEnderecosPage from '@/pages/Clientes/ClienteEnderecosPage';
import ClienteCreditoPage from '@/pages/Clientes/ClienteCreditoPage';
import { ProdutosPage, ProdutoFormPage, ProdutoDetalhesPage, ProdutoVariantesPage, CategoriasPage } from '@/pages/Produtos';
import { LojaOnlinePublicoPage, ProdutoDetalhePage, CarrinhoPage, CheckoutPage, RastreamentoPedidoPage, MeusPedidosPage, ClientePerfilPage, ClienteLoginPage } from '@/pages/LojaOnlinePublico';
import { PedidosOnlinePage, ConfiguracoesLojaPage } from '@/pages/LojaOnline';
import { EmpresaPage, UsuariosPage, IntegracoesPage } from '@/pages/Configuracoes';
import { EstoquePage, EstoqueDetalhePage } from '@/pages/Estoque';
import { VendasPage } from '@/pages/Vendas';
import { FinanceiroPage } from '@/pages/Financeiro';
import MainLayout from '@/components/layout/MainLayout/MainLayout';
import RoleProtectedRoute from '@/components/common/RoleProtectedRoute';

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
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

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

        {/* Loja Online Pública (sem autenticação) */}
        <Route path="/c/:empresaSlug" element={<LojaOnlinePublicoPage />} />
        <Route path="/c/:empresaSlug/login" element={<ClienteLoginPage />} />
        <Route path="/c/:empresaSlug/produto/:produtoId" element={<ProdutoDetalhePage />} />
        <Route path="/c/:empresaSlug/carrinho" element={<CarrinhoPage />} />
        <Route path="/c/:empresaSlug/checkout" element={<CheckoutPage />} />
        <Route path="/c/:empresaSlug/pedido/:numeroPedido" element={<RastreamentoPedidoPage />} />
        
        {/* Área do Cliente Autenticado */}
        <Route path="/c/:empresaSlug/minha-conta/pedidos" element={<MeusPedidosPage />} />
        <Route path="/c/:empresaSlug/minha-conta/perfil" element={<ClientePerfilPage />} />

        {/* OAuth Callback Routes - Cliente */}
        <Route path="/auth/callback/google" element={<GoogleCallback />} />
        <Route path="/auth/callback/microsoft" element={<MicrosoftCallback />} />

        {/* OAuth Callback Route */}
        <Route path="/auth/callback" element={<OAuthCallbackPage />} />

        {/* Password Recovery Routes */}
        <Route
          path="/forgot-password"
          element={
            <PublicRoute>
              <ForgotPasswordPage />
            </PublicRoute>
          }
        />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

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
          
          {/* Rota de Perfil - Todos os usuários */}
          <Route path="perfil" element={<PerfilPage />} />
          
          {/* Rotas de Clientes */}
          <Route path="clientes" element={<ClientesPage />} />
          <Route path="clientes/novo" element={<ClienteFormPage />} />
          <Route path="clientes/:id" element={<ClienteFormPage />} />
          <Route path="clientes/:id/editar" element={<ClienteFormPage />} />
          <Route path="clientes/:id/enderecos" element={<ClienteEnderecosPage />} />
          <Route path="clientes/:id/credito" element={<ClienteCreditoPage />} />
          
          {/* Rotas de Loja Online */}
          <Route path="loja/pedidos" element={<PedidosOnlinePage />} />
          <Route path="loja/configuracoes" element={<ConfiguracoesLojaPage />} />
          
          {/* Rotas de Produtos */}
          <Route path="produtos" element={<ProdutosPage />} />
          <Route path="produtos/novo" element={<ProdutoFormPage />} />
          <Route path="produtos/:id" element={<ProdutoDetalhesPage />} />
          <Route path="produtos/:id/editar" element={<ProdutoFormPage />} />
          <Route path="produtos/:id/variantes" element={<ProdutoVariantesPage />} />
          <Route path="categorias" element={<CategoriasPage />} />
          
          {/* Rotas de Estoque - ADMIN e OPERADOR */}
          <Route
            path="estoque"
            element={
              <RoleProtectedRoute requiredRole={['ADMIN', 'OPERADOR']}>
                <EstoquePage />
              </RoleProtectedRoute>
            }
          />
          <Route
            path="estoque/:id"
            element={
              <RoleProtectedRoute requiredRole={['ADMIN', 'OPERADOR']}>
                <EstoqueDetalhePage />
              </RoleProtectedRoute>
            }
          />

          {/* Rotas de Vendas - ADMIN e OPERADOR */}
          <Route
            path="vendas"
            element={
              <RoleProtectedRoute requiredRole={['ADMIN', 'OPERADOR']}>
                <VendasPage />
              </RoleProtectedRoute>
            }
          />

          {/* Rotas de Financeiro - Apenas ADMIN */}
          <Route
            path="financeiro"
            element={
              <RoleProtectedRoute requiredRole={['ADMIN']}>
                <FinanceiroPage />
              </RoleProtectedRoute>
            }
          />
          
          {/* Rotas de Configurações - Apenas ADMIN */}
          <Route 
            path="configuracoes/empresa" 
            element={
              <RoleProtectedRoute requiredRole={['ADMIN']}>
                <EmpresaPage />
              </RoleProtectedRoute>
            } 
          />
          <Route 
            path="configuracoes/usuarios" 
            element={
              <RoleProtectedRoute requiredRole={['ADMIN']}>
                <UsuariosPage />
              </RoleProtectedRoute>
            } 
          />
          <Route 
            path="configuracoes/integracoes" 
            element={
              <RoleProtectedRoute requiredRole={['ADMIN']}>
                <IntegracoesPage />
              </RoleProtectedRoute>
            } 
          />
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
