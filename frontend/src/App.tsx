import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { ehPainelPlataforma, separarPorHost, escolherPorta } from '@/config/host';
import LoginPage from '@/pages/Login/LoginPage';
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

// O painel da plataforma só é baixado no subdomínio dele: lazy separa o chunk,
// e o host decide se alguma rota chega a pedi-lo.
const PlataformaPage = lazy(() => import('@/pages/Plataforma/PlataformaPage'));
const PlataformaDashboard = lazy(() => import('@/pages/Plataforma/PlataformaDashboard'));

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
  const { pathname } = useLocation();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Uma porta só, em vez de um guard por rota: tela nova nasce fechada para quem
  // não é daquele host sem ninguém lembrar de fechá-la.
  switch (escolherPorta(user?.role, ehPainelPlataforma, pathname, separarPorHost)) {
    case 'para-plataforma':
      return <Navigate to="/plataforma" replace />;
    case 'para-dashboard':
      return <Navigate to="/dashboard" replace />;
    case 'porta-errada':
      return <PortaErrada />;
  }

  return <>{children}</>;
};

/**
 * Conta certa, endereço errado — o super admin no domínio do lojista, ou o
 * lojista no domínio do painel. Uma tela, e não um redirect, porque redirecionar
 * para o outro host levaria a sessão junto: o cookie é host-only e não existe lá.
 */
const PortaErrada: React.FC = () => {
  const { user, logout } = useAuth();
  const ehSuper = user?.role === 'SUPER_ADMIN';

  return (
    <div className="empty-state" style={{ minHeight: '100vh', display: 'grid', placeContent: 'center', textAlign: 'center', gap: '1rem', padding: '2rem' }}>
      <h2>Endereço errado</h2>
      <p>
        {ehSuper
          ? 'Esta conta administra a plataforma. Entre pelo subdomínio de administração.'
          : 'Este endereço é o painel da plataforma. Entre pelo endereço do seu ERP.'}
      </p>
      <button className="btn btn-primary" onClick={logout}>Sair</button>
    </div>
  );
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
      <Suspense fallback={<LoadingScreen />}>
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
          {/* Painel da plataforma - Apenas SUPER_ADMIN (sem empresa_id, nenhuma tela de tenant funciona para ele) */}
          <Route
            path="plataforma"
            element={
              <RoleProtectedRoute requiredRole={['SUPER_ADMIN']}>
                <PlataformaDashboard />
              </RoleProtectedRoute>
            }
          />
          <Route
            path="plataforma/tenants"
            element={
              <RoleProtectedRoute requiredRole={['SUPER_ADMIN']}>
                <PlataformaPage />
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
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
