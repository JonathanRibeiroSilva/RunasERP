import { useState, useEffect, ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  FiUser, 
  FiPackage, 
  FiLogOut, 
  FiMenu,
  FiX,
  FiHome,
  FiShoppingCart
} from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { toast } from 'react-toastify';
import { useCarrinho } from '@/hooks/useCarrinho';
import './ClienteLayout.scss';

interface ClienteInfo {
  id: string;
  nome: string;
  email: string;
  telefone?: string;
  cpf?: string;
}

interface ClienteLayoutProps {
  children: ReactNode;
  title?: string;
}

/**
 * Layout para área autenticada do cliente
 * Inclui navbar com perfil, menu e logout
 */
const ClienteLayout = ({ children, title }: ClienteLayoutProps) => {
  const navigate = useNavigate();
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const { carrinho } = useCarrinho({ empresaSlug });
  
  const [cliente, setCliente] = useState<ClienteInfo | null>(null);
  const [menuAberto, setMenuAberto] = useState(false);
  const [dropdownAberto, setDropdownAberto] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    verificarAutenticacao();
  }, []);

  const verificarAutenticacao = async () => {
    try {
      const response = await apiPublica.get('/clientes/me');
      setCliente(response.data);
    } catch {
      // Não autenticado - redirecionar para login
      toast.error('Você precisa estar logado para acessar esta página');
      navigate(`/c/${empresaSlug}/login`, { 
        state: { from: window.location.pathname } 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiPublica.post('/auth/cliente/logout');
      toast.success('Você saiu da sua conta');
      navigate(`/c/${empresaSlug}`);
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
      toast.error('Erro ao sair');
    }
  };

  const handleNavegar = (path: string) => {
    navigate(path);
    setMenuAberto(false);
    setDropdownAberto(false);
  };

  if (loading) {
    return (
      <div className="cliente-layout loading">
        <div className="spinner" />
        <p>Carregando...</p>
      </div>
    );
  }

  if (!cliente) {
    return null; // Será redirecionado
  }

  return (
    <div className="cliente-layout">
      {/* Navbar */}
      <nav className="cliente-navbar">
        <div className="navbar-container">
          {/* Logo/Voltar para Loja */}
          <div className="navbar-brand" onClick={() => handleNavegar(`/c/${empresaSlug}`)}>
            <FiHome />
            <span>Voltar para Loja</span>
          </div>

          {/* Menu Mobile Toggle */}
          <button 
            className="menu-toggle"
            onClick={() => setMenuAberto(!menuAberto)}
          >
            {menuAberto ? <FiX /> : <FiMenu />}
          </button>

          {/* Menu */}
          <div className={`navbar-menu ${menuAberto ? 'aberto' : ''}`}>
            {/* Carrinho */}
            <button 
              className="navbar-item"
              onClick={() => handleNavegar(`/c/${empresaSlug}/carrinho`)}
            >
              <FiShoppingCart />
              <span>Carrinho</span>
              {carrinho && carrinho.quantidade_itens > 0 && (
                <span className="badge">{carrinho.quantidade_itens}</span>
              )}
            </button>

            {/* Meus Pedidos */}
            <button 
              className="navbar-item"
              onClick={() => handleNavegar(`/c/${empresaSlug}/minha-conta/pedidos`)}
            >
              <FiPackage />
              <span>Meus Pedidos</span>
            </button>

            {/* Dropdown do Perfil */}
            <div className="navbar-item dropdown">
              <button 
                className="dropdown-toggle"
                onClick={() => setDropdownAberto(!dropdownAberto)}
                onBlur={() => setTimeout(() => setDropdownAberto(false), 200)}
              >
                <FiUser />
                <span>{cliente.nome.split(' ')[0]}</span>
              </button>

              {dropdownAberto && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    <strong>{cliente.nome}</strong>
                    <span className="email">{cliente.email}</span>
                    {cliente.telefone && (
                      <span className="telefone">{cliente.telefone}</span>
                    )}
                  </div>
                  <div className="dropdown-divider" />
                  <button 
                    className="dropdown-item"
                    onClick={() => handleNavegar(`/c/${empresaSlug}/minha-conta/perfil`)}
                  >
                    <FiUser />
                    Meu Perfil
                  </button>
                  <button 
                    className="dropdown-item"
                    onClick={() => handleNavegar(`/c/${empresaSlug}/minha-conta/pedidos`)}
                  >
                    <FiPackage />
                    Meus Pedidos
                  </button>
                  <div className="dropdown-divider" />
                  <button 
                    className="dropdown-item logout"
                    onClick={handleLogout}
                  >
                    <FiLogOut />
                    Sair
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Conteúdo */}
      <main className="cliente-content">
        {title && (
          <div className="content-header">
            <h1>{title}</h1>
          </div>
        )}
        {children}
      </main>

      {/* Footer */}
      <footer className="cliente-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default ClienteLayout;
