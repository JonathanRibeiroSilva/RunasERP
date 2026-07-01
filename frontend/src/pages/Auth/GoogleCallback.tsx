import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { apiPublica } from '@/services/api/apiPublica';
import { getErrorMessage } from '@/services/api/axios';
import { Toast } from '@/utils/toast';
import './AuthCallback.scss';

const GoogleCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [processando, setProcessando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    const processarCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const savedState = sessionStorage.getItem('oauth_state');
      const empresaSlug = sessionStorage.getItem('oauth_empresa_slug');

      if (!code || !state) {
        setErro('Parâmetros inválidos');
        setProcessando(false);
        return;
      }

      if (state !== savedState) {
        setErro('State inválido - possível ataque CSRF');
        setProcessando(false);
        return;
      }

      if (!empresaSlug) {
        setErro('Sessão expirada');
        setProcessando(false);
        return;
      }

      try {
        const response = await apiPublica.post('/auth/cliente/oauth/google/callback', {
          code,
          state,
        }, {
          withCredentials: true  // ✅ Importante: permite cookies HTTP-only
        });

        const { cliente } = response.data;

        // ✅ Backend setou cookies HTTP-only automaticamente
        // ❌ NÃO usar localStorage (vulnerável a XSS)

        // Get return URL (where user was before OAuth)
        const returnUrl = sessionStorage.getItem('oauth_return_url') || `/c/${empresaSlug}/checkout`;

        // Limpar dados OAuth do sessionStorage
        sessionStorage.removeItem('oauth_state');
        sessionStorage.removeItem('oauth_empresa_slug');
        sessionStorage.removeItem('oauth_return_url');

        // Sinalizar para recarregar carrinho após retornar
        sessionStorage.setItem('reload_cart_after_oauth', 'true');

        Toast.success(`Bem-vindo, ${cliente.nome}!`);

        // Redirecionar para onde o usuário estava (geralmente checkout com carrinho)
        navigate(returnUrl);
      } catch (error) {
        const mensagem = getErrorMessage(error, 'Erro ao processar login');
        setErro(mensagem);
        Toast.error(mensagem);
        setProcessando(false);

        // Redirecionar para checkout após 3 segundos
        setTimeout(() => {
          navigate(`/c/${empresaSlug}/checkout`);
        }, 3000);
      }
    };

    processarCallback();
  }, [searchParams, navigate]);

  return (
    <div className="auth-callback">
      <div className="auth-callback-card">
        {processando && (
          <>
            <div className="spinner"></div>
            <h2>Processando login...</h2>
            <p>Aguarde enquanto validamos suas credenciais</p>
          </>
        )}

        {!processando && erro && (
          <>
            <div className="error-icon">❌</div>
            <h2>Erro no login</h2>
            <p>{erro}</p>
            <p className="redirect-info">Redirecionando em 3 segundos...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default GoogleCallback;
