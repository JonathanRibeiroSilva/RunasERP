import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Página que redireciona para o catálogo público da empresa.
 * TODO: Buscar o slug da empresa do usuário logado.
 */
const CatalogoRedirectPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // TODO: Pegar o empresa_id do usuário e buscar o slug
    // Por enquanto, usar slug padrão
    const empresaSlug = 'distribuidora-central';
    
    // Abrir em nova aba
    window.open(`/c/${empresaSlug}`, '_blank');
    
    // Voltar para a página anterior
    navigate(-1);
  }, [navigate]);

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
