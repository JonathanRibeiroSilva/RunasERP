import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  FiHome,
  FiUsers,
  FiPackage,
  FiShoppingCart,
  FiBox,
  FiDollarSign,
  FiX,
  FiChevronDown,
  FiChevronRight,
  FiGlobe,
  FiShoppingBag,
  FiSettings,
  FiTag,
  FiBriefcase,
  FiUserPlus,
  FiZap,
  FiUser,
  FiExternalLink,
} from 'react-icons/fi';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/types/auth';
import './Sidebar.scss';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
  isMobile?: boolean;
}

interface SubMenuItem {
  path?: string;
  icon: React.ReactNode;
  label: string;
  requiredRole?: UserRole[]; // Roles que podem ver este item
  external?: boolean; // Se é link externo
  action?: () => void; // Ação customizada (ex: abrir nova aba)
}

interface NavItem {
  path?: string;
  icon: React.ReactNode;
  label: string;
  submenu?: SubMenuItem[];
  requiredRole?: UserRole[]; // Roles que podem ver este item
}

const navItems: NavItem[] = [
  { 
    path: '/dashboard', 
    icon: <FiHome />, 
    label: 'Dashboard' 
  },
  { 
    path: '/clientes', 
    icon: <FiUsers />, 
    label: 'Clientes' 
  },
  { 
    icon: <FiGlobe />, 
    label: 'Loja Online',
    submenu: [
      { 
        icon: <FiExternalLink />, 
        label: 'Minha Loja',
        external: true,
        action: () => window.open('/c/distribuidora-central', '_blank') // TODO: Usar empresa_slug dinâmico
      },
      { path: '/loja/pedidos', icon: <FiShoppingBag />, label: 'Pedidos Online' },
      { path: '/loja/configuracoes', icon: <FiSettings />, label: 'Configurações da Loja' },
    ]
  },
  { 
    icon: <FiPackage />, 
    label: 'Produtos',
    submenu: [
      { path: '/produtos', icon: <FiPackage />, label: 'Produtos' },
      { path: '/categorias', icon: <FiTag />, label: 'Categorias' },
    ]
  },
  { 
    path: '/estoque', 
    icon: <FiBox />, 
    label: 'Estoque' 
  },
  { 
    path: '/vendas', 
    icon: <FiShoppingCart />, 
    label: 'Vendas' 
  },
  { 
    path: '/financeiro', 
    icon: <FiDollarSign />, 
    label: 'Financeiro' 
  },
  // CONFIGURAÇÕES - Apenas ADMIN
  { 
    icon: <FiSettings />, 
    label: 'Configurações',
    requiredRole: ['ADMIN'], // ← Apenas ADMIN vê
    submenu: [
      { path: '/configuracoes/empresa', icon: <FiBriefcase />, label: 'Empresa' },
      { path: '/configuracoes/usuarios', icon: <FiUserPlus />, label: 'Usuários' },
      { path: '/configuracoes/integracoes', icon: <FiZap />, label: 'Integrações' },
    ]
  },
  // MEU PERFIL - Todos os usuários
  {
    path: '/perfil',
    icon: <FiUser />,
    label: 'Meu Perfil'
  },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, isMobile = false }) => {
  const location = useLocation();
  const { user } = useAuth(); // ← Pegar usuário atual
  
  const [expandedMenus, setExpandedMenus] = useState<string[]>(() => {
    // Inicializar estado com submenus ativos na primeira renderização
    const initialExpanded: string[] = [];
    navItems.forEach(item => {
      if (item.submenu && item.submenu.some(subItem => location.pathname.startsWith(subItem.path))) {
        initialExpanded.push(item.label);
      }
    });
    return initialExpanded;
  });

  // Função para verificar se o usuário tem permissão para ver o item
  const canViewItem = (requiredRole?: UserRole[]): boolean => {
    if (!requiredRole || requiredRole.length === 0) return true; // Sem restrição
    if (!user) return false; // Sem usuário logado
    return requiredRole.includes(user.role); // Verifica se role está na lista
  };

  // Filtrar items baseado em permissão
  const visibleNavItems = navItems.filter(item => canViewItem(item.requiredRole));

  const handleNavClick = () => {
    // Fechar sidebar automaticamente ao clicar em link no mobile
    if (isMobile && onClose) {
      onClose();
    }
  };

  const toggleSubmenu = (label: string, submenu?: SubMenuItem[]) => {
    // Se está colapsado, expande
    if (!expandedMenus.includes(label)) {
      setExpandedMenus(prev => [...prev, label]);
    } else {
      // Se está expandido, colapsa
      setExpandedMenus(prev => prev.filter(item => item !== label));
    }
  };

  const isSubmenuActive = (submenu: SubMenuItem[]) => {
    return submenu.some(item => location.pathname.startsWith(item.path));
  };

  const isMenuExpanded = (label: string, submenu?: SubMenuItem[]) => {
    // Permitir colapso manual mesmo se rota está ativa
    return expandedMenus.includes(label);
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
        {visibleNavItems.map((item) => {
          // Filtrar submenus baseado em permissão
          const visibleSubmenu = item.submenu?.filter(subItem => canViewItem(subItem.requiredRole));
          
          return (
            <div key={item.label} className="nav-item-wrapper">
              {/* Item com submenu */}
              {visibleSubmenu && visibleSubmenu.length > 0 ? (
                <>
                  <button
                    className={`nav-item nav-item-parent ${isSubmenuActive(visibleSubmenu) ? 'active' : ''}`}
                    onClick={() => toggleSubmenu(item.label, visibleSubmenu)}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                    <span className="nav-arrow">
                      {isMenuExpanded(item.label, visibleSubmenu) ? <FiChevronDown /> : <FiChevronRight />}
                    </span>
                  </button>
                  
                  {/* Submenu */}
                  <div className={`nav-submenu ${isMenuExpanded(item.label, visibleSubmenu) ? 'expanded' : ''}`}>
                    {visibleSubmenu.map((subItem, index) => {
                      // Item externo (ex: Ver Minha Loja)
                      if (subItem.external && subItem.action) {
                        return (
                          <button
                            key={subItem.label}
                            onClick={() => {
                              subItem.action?.();
                              handleNavClick();
                            }}
                            className="nav-subitem nav-subitem-external"
                          >
                            <span className="nav-icon">{subItem.icon}</span>
                            <span className="nav-label">{subItem.label}</span>
                          </button>
                        );
                      }
                      
                      // Item normal (NavLink)
                      return (
                        <NavLink
                          key={subItem.path || index}
                          to={subItem.path!}
                          onClick={handleNavClick}
                          className={({ isActive }) => `nav-subitem ${isActive ? 'active' : ''}`}
                        >
                          <span className="nav-icon">{subItem.icon}</span>
                          <span className="nav-label">{subItem.label}</span>
                        </NavLink>
                      );
                    })}
                  </div>
                </>
              ) : (
                /* Item direto (sem submenu) */
                item.path && (
                  <NavLink
                    to={item.path}
                    onClick={handleNavClick}
                    className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                  </NavLink>
                )
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
};

export default Sidebar;
