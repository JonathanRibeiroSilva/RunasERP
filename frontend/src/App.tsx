import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoginPage from '@/pages/Login/LoginPage';
import RegisterPage from '@/pages/Register/RegisterPage';
import OAuthCallbackPage from '@/pages/Auth/OAuthCallbackPage';
import ForgotPasswordPage from '@/pages/Auth/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/Auth/ResetPasswordPage';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import ClientesPage from '@/pages/Clientes/ClientesPage';
import ClienteFormPage from '@/pages/Clientes/ClienteFormPage';
import ClienteEnderecosPage from '@/pages/Clientes/ClienteEnderecosPage';
import ClienteCreditoPage from '@/pages/Clientes/ClienteCreditoPage';
import { ProdutosPage, ProdutoFormPage, ProdutoDetalhesPage, ProdutoVariantesPage, CategoriasPage } from '@/pages/Produtos';
import { CatalogoPage, ProdutoDetalhePage, CarrinhoPage, CheckoutPage, RastreamentoPedidoPage, MeusPedidosPage } from '@/pages/CatalogoPublico';
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

        {/* Catálogo Público (sem autenticação) */}
        <Route path="/c/:empresaSlug" element={<CatalogoPage />} />
        <Route path="/c/:empresaSlug/produto/:produtoId" element={<ProdutoDetalhePage />} />
        <Route path="/c/:empresaSlug/carrinho" element={<CarrinhoPage />} />
        <Route path="/c/:empresaSlug/checkout" element={<CheckoutPage />} />
        <Route path="/c/:empresaSlug/pedido/:numeroPedido" element={<RastreamentoPedidoPage />} />
        <Route path="/c/:empresaSlug/minha-conta/pedidos" element={<MeusPedidosPage />} />

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
          
          {/* Rotas de Clientes */}
          <Route path="clientes" element={<ClientesPage />} />
          <Route path="clientes/novo" element={<ClienteFormPage />} />
          <Route path="clientes/:id" element={<ClienteFormPage />} />
          <Route path="clientes/:id/editar" element={<ClienteFormPage />} />
          <Route path="clientes/:id/enderecos" element={<ClienteEnderecosPage />} />
          <Route path="clientes/:id/credito" element={<ClienteCreditoPage />} />
          {/* TODO: Implementar página de histórico */}
          {/* <Route path="clientes/:id/historico" element={<ClienteHistoricoPage />} /> */}
          
          {/* Rotas de Produtos - Sprint 2 */}
          <Route path="produtos" element={<ProdutosPage />} />
          <Route path="produtos/novo" element={<ProdutoFormPage />} />
          <Route path="produtos/:id" element={<ProdutoDetalhesPage />} />
          <Route path="produtos/:id/editar" element={<ProdutoFormPage />} />
          <Route path="produtos/:id/variantes" element={<ProdutoVariantesPage />} />
          <Route path="categorias" element={<CategoriasPage />} />
          
          {/* Rotas de Estoque - Sprint 3 */}
          {/* TODO: Implementar páginas de estoque */}
          {/* <Route path="estoque" element={<EstoquePage />} /> */}
          {/* <Route path="estoque/movimentacoes" element={<EstoqueMovimentacoesPage />} /> */}
          {/* <Route path="estoque/entrada" element={<EstoqueEntradaPage />} /> */}
          {/* <Route path="estoque/lotes" element={<EstoqueLotesPage />} /> */}
          {/* <Route path="estoque/inventario" element={<EstoqueInventarioPage />} /> */}
          
          {/* Rotas de Vendas - Sprint 5 */}
          {/* TODO: Implementar páginas de vendas */}
          {/* <Route path="vendas" element={<VendasPage />} /> */}
          {/* <Route path="vendas/nova" element={<PDVPage />} /> */}
          {/* <Route path="vendas/:id" element={<VendaDetalhesPage />} /> */}
          
          {/* Rotas de Financeiro - Sprint 7 */}
          {/* TODO: Implementar páginas financeiras */}
          {/* <Route path="financeiro" element={<FinanceiroDashboard />} /> */}
          {/* <Route path="financeiro/contas-receber" element={<ContasReceberPage />} /> */}
          {/* <Route path="financeiro/contas-pagar" element={<ContasPagarPage />} /> */}
        </Route>

        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
