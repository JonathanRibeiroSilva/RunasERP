import { NavLink } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiPackage,
  FiShoppingCart,
  FiBox,
  FiDollarSign,
} from 'react-icons/fi';
import './Sidebar.scss';

interface SidebarProps {
  isOpen: boolean;
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
  { path: '/vendas', icon: <FiShoppingCart />, label: 'Vendas' },
  { path: '/estoque', icon: <FiBox />, label: 'Estoque' },
  { path: '/financeiro', icon: <FiDollarSign />, label: 'Financeiro' },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
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
