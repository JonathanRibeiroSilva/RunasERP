import { useAuth } from '@/hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { FiMenu, FiX, FiLogOut, FiShield, FiCompass, FiSettings, FiArrowLeft, FiUser } from 'react-icons/fi';
import logoImg from '@/img/logo1.png';
import './Navbar.scss';

interface NavbarProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-capsule">
        {/* Left Side */}
        <div className="nav-left">
          <button 
            className="nav-btn" 
            onClick={onToggleSidebar}
            aria-label="Toggle Menu"
          >
            {sidebarOpen ? <FiX className="icon-sm" /> : <FiArrowLeft className="icon-sm" />}
            <span>DASHBOARD</span>
          </button>
          
          <div className="nav-divider"></div>

          <div className="nav-brand">
            <img src={logoImg} alt="Runas" className="nav-logo" />
            <span className="brand-text">RUNAS</span>
          </div>
        </div>

        {/* Center - Empty */}
        <div className="nav-center">
        </div>

        {/* Right Side */}
        <div className="nav-right">
          <div 
            className="user-block" 
            onClick={() => navigate('/perfil')}
            title="Acessar Meu Perfil"
          >
            <FiUser className="user-avatar" />
            <span className="user-name">{(user?.nome || 'SILENTZ').replace(/\[(?:ADMIN|OPERADOR)\]/gi, '').trim()}</span>
          </div>

          <button className="nav-btn logout-btn" onClick={handleLogout}>
            <FiLogOut className="icon-sm" />
            <span>LOGOUT</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
