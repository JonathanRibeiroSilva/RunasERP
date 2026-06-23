import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import type { UserRole } from '@/types/auth';
import { toast } from 'react-toastify';
import { useEffect, useState } from 'react';

interface RoleProtectedRouteProps {
  children: React.ReactNode;
  requiredRole: UserRole[];
}

/**
 * Componente que protege rotas baseado em role do usuário.
 * Redireciona para dashboard se o usuário não tiver a role necessária.
 */
const RoleProtectedRoute: React.FC<RoleProtectedRouteProps> = ({ children, requiredRole }) => {
  const { user } = useAuth();
  const [hasShownToast, setHasShownToast] = useState(false);

  const hasPermission = user && requiredRole.includes(user.role);

  useEffect(() => {
    if (!hasPermission && !hasShownToast) {
      toast.error('Você não tem permissão para acessar esta página.', {
        toastId: 'role-denied', // Evita toasts duplicados
      });
      setHasShownToast(true);
    }
  }, [hasPermission, hasShownToast]);

  if (!hasPermission) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default RoleProtectedRoute;
