import { useAuth } from '@/hooks/useAuth';
import { FiMenu, FiX, FiLogOut, FiUser } from 'react-icons/fi';
import './Navbar.scss';

interface NavbarProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar, sidebarOpen }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-content">
        {/* Left Side */}
        <div className="navbar-left">
          <button 
            className={`btn-icon sidebar-toggle ${sidebarOpen ? 'active' : ''}`} 
            onClick={onToggleSidebar} 
            aria-label={sidebarOpen ? 'Fechar menu' : 'Abrir menu'}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? <FiX /> : <FiMenu />}
          </button>
          <h1 className="navbar-title">Runas</h1>
        </div>

        {/* Right Side */}
        <div className="navbar-right">
          <div className="user-info">
            <FiUser className="user-icon" />
            <div className="user-details">
              <span className="user-name">{user?.nome}</span>
              <span className="user-role">{user?.role}</span>
            </div>
          </div>

          <button className="btn-icon btn-logout" onClick={handleLogout} aria-label="Sair">
            <FiLogOut />
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
