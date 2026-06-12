import { NavLink } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiPackage,
  FiShoppingCart,
  FiBox,
  FiDollarSign,
  FiFolder,
  FiX,
} from 'react-icons/fi';
import './Sidebar.scss';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
  isMobile?: boolean;
}

interface NavItem {
  path: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { path: '/dashboard', icon: <FiHome />, label: 'Dashboard' },
  { path: '/clientes', icon: <FiUsers />, label: 'Clientes' },
  { path: '/produtos', icon: <FiPackage />, label: 'Produtos' },
  { path: '/categorias', icon: <FiFolder />, label: 'Categorias' },
  { path: '/vendas', icon: <FiShoppingCart />, label: 'Vendas' },
  { path: '/estoque', icon: <FiBox />, label: 'Estoque' },
  { path: '/financeiro', icon: <FiDollarSign />, label: 'Financeiro' },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, isMobile = false }) => {
  const handleNavClick = () => {
    // Fechar sidebar automaticamente ao clicar em link no mobile
    if (isMobile && onClose) {
      onClose();
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      {/* Botão fechar (apenas mobile) */}
      {isMobile && isOpen && onClose && (
        <button 
          className="sidebar-close" 
          onClick={onClose} 
          aria-label="Fechar menu"
        >
          <FiX />
        </button>
      )}
      
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            onClick={handleNavClick}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
