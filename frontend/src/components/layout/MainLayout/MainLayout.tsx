import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '../Navbar/Navbar';
import Sidebar from '../Sidebar/Sidebar';
import ErrorBoundary from '@/components/common/ErrorBoundary/ErrorBoundary';
import './MainLayout.scss';

const MainLayout = () => {
  const location = useLocation();
  // Detectar se é mobile (< 768px)
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  // Sidebar aberta por padrão no desktop, fechada no mobile
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      
      // Auto-abrir sidebar no desktop se estava fechada
      if (!mobile && !sidebarOpen) {
        setSidebarOpen(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [sidebarOpen]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const closeSidebar = () => {
    // Fechar sidebar apenas no mobile
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  // Impedir scroll do body quando sidebar aberta no mobile
  useEffect(() => {
    if (isMobile && sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobile, sidebarOpen]);

  return (
    <div className="main-layout">
      <Navbar onToggleSidebar={toggleSidebar} sidebarOpen={sidebarOpen} />
      
      {/* Backdrop para mobile - fecha sidebar ao clicar */}
      {isMobile && sidebarOpen && (
        <div 
          className="sidebar-backdrop" 
          onClick={closeSidebar}
          role="button"
          aria-label="Fechar menu"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              closeSidebar();
            }
          }}
        />
      )}
      
      <div className="layout-container">
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={closeSidebar} 
          isMobile={isMobile} 
        />
        <main className={`main-content ${sidebarOpen && !isMobile ? 'sidebar-open' : ''}`}>
          <div className="content-wrapper">
            <ErrorBoundary key={location.pathname}>
              <Outlet />
            </ErrorBoundary>
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
