import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useEmpresa } from '@/hooks/useLojaOnline';

/**
 * Página que redireciona para o catálogo público da empresa do usuário logado.
 * O slug vem do cache do React Query (atualizado ao renomear a loja); o slug
 * do /auth/me é só fallback enquanto a query carrega.
 */
const CatalogoRedirectPage = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: empresa, isLoading } = useEmpresa(user?.empresa_id);

  useEffect(() => {
    if (isLoading) return;
    const lojaSlug = empresa?.slug ?? user?.empresa_slug;
    if (lojaSlug) {
      window.open(`/c/${lojaSlug}`, '_blank', 'noopener');
    }
    // Voltar para a página anterior
    navigate(-1);
  }, [navigate, user, empresa, isLoading]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px',
      color: '#9CA3AF'
    }}>
      <p>Abrindo catálogo público...</p>
    </div>
  );
};

export default CatalogoRedirectPage;
