import { useNavigate, useParams } from 'react-router-dom';
import { FiUser } from 'react-icons/fi';
import './LojaNavBar.scss';

interface LojaNavBarProps {
  showLoginButton?: boolean;
}

/**
 * Navbar simples para loja pública - apenas botão de login
 */
const LojaNavBar = ({ showLoginButton = true }: LojaNavBarProps) => {
  const navigate = useNavigate();
  const { empresaSlug } = useParams<{ empresaSlug: string }>();

  const handleLogin = () => {
    navigate(`/c/${empresaSlug}/login`, { 
      state: { from: window.location.pathname } 
    });
  };

  if (!showLoginButton) {
    return null;
  }

  return (
    <div className="loja-login-button">
      <button 
        className="btn-entrar"
        onClick={handleLogin}
        title="Entrar na sua conta"
      >
        <FiUser />
        <span>Entrar</span>
      </button>
    </div>
  );
};

export default LojaNavBar;
