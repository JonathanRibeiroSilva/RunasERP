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
  FiGrid,
} from 'react-icons/fi';
import { useAuth } from '@/hooks/useAuth';
import { useEmpresa } from '@/hooks/useLojaOnline';
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
  openStore?: boolean; // Abre a loja online da empresa em nova aba
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
        openStore: true,
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
    label: 'Financeiro',
    requiredRole: ['ADMIN'], // ← Apenas ADMIN vê
  },
  // PLATAFORMA - Apenas SUPER_ADMIN
  {
    path: '/plataforma',
    icon: <FiGrid />,
    label: 'Plataforma',
    requiredRole: ['SUPER_ADMIN'],
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
  // MEU PERFIL - Todos os usuários, super admin incluído (troca de senha dele)
  {
    path: '/perfil',
    icon: <FiUser />,
    label: 'Meu Perfil',
    requiredRole: ['ADMIN', 'OPERADOR', 'SUPER_ADMIN'],
  },
];

/**
 * Quem vê cada item do menu.
 *
 * Item sem requiredRole é item de tenant (loja, produtos, estoque, vendas): o
 * SUPER_ADMIN não tem empresa_id, então essas telas consultariam uma empresa que
 * ele não tem. Negar por omissão vale mais que marcar item por item — item novo
 * nasce fora do painel de plataforma sem ninguém lembrar de fechá-lo.
 */
export const podeVer = (role: UserRole | undefined, requiredRole?: UserRole[]): boolean => {
  if (!role) return false;
  if (!requiredRole || requiredRole.length === 0) return role !== 'SUPER_ADMIN';
  return requiredRole.includes(role);
};

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, isMobile = false }) => {
  const location = useLocation();
  const { user } = useAuth(); // ← Pegar usuário atual
  // Slug via React Query: acompanha a renomeação da loja sem precisar relogar
  // (useAtualizarEmpresa invalida ['empresa', id] ao salvar as configurações)
  const { data: empresa } = useEmpresa(user?.empresa_id);
  const lojaSlug = empresa?.slug ?? user?.empresa_slug;

  const abrirMinhaLoja = () => {
    if (lojaSlug) {
      window.open(`/c/${lojaSlug}`, '_blank', 'noopener');
    }
  };

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

  const canViewItem = (requiredRole?: UserRole[]) => podeVer(user?.role, requiredRole);

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
                      if (subItem.external && subItem.openStore) {
                        return (
                          <button
                            key={subItem.label}
                            onClick={() => {
                              abrirMinhaLoja();
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
