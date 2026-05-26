import { useAuth } from '@/hooks/useAuth';
import { FiMenu, FiLogOut, FiUser } from 'react-icons/fi';
import './Navbar.scss';

interface NavbarProps {
  onToggleSidebar: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
  };

  return (
    <nav className="navbar">
      <div className="navbar-content">
        {/* Left Side */}
        <div className="navbar-left">
          <button className="btn-icon" onClick={onToggleSidebar} aria-label="Toggle sidebar">
            <FiMenu />
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

          <button className="btn-icon btn-logout" onClick={handleLogout} aria-label="Logout">
            <FiLogOut />
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
