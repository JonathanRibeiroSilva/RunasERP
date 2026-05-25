import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { oauthService } from '@/services/auth/oauthService';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'react-toastify';
import { getErrorMessage } from '@/services/api/axios';
import './OAuthCallbackPage.scss';

const OAuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Obter code e state da URL
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const errorParam = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');

        // Verificar se houve erro do provider
        if (errorParam) {
          throw new Error(errorDescription || errorParam);
        }

        // Verificar se code e state existem
        if (!code || !state) {
          throw new Error('Parâmetros OAuth inválidos');
        }

        // Processar callback
        const response = await oauthService.handleOAuthCallback(code, state);

        // Atualizar contexto de autenticação
        // (os tokens já foram salvos pelo oauthService)
        toast.success(`Bem-vindo, ${response.user.nome}!`);

        // Redirecionar para dashboard
        navigate('/dashboard', { replace: true });
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        toast.error(`Erro no login: ${message}`);

        // Redirecionar para login após 3 segundos
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, login]);

  return (
    <div className="oauth-callback-page">
      <div className="callback-container">
        {error ? (
          <div className="callback-error">
            <div className="error-icon">❌</div>
            <h2>Erro na Autenticação</h2>
            <p>{error}</p>
            <p className="redirect-message">Redirecionando para login...</p>
          </div>
        ) : (
          <div className="callback-loading">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Carregando...</span>
            </div>
            <h2>Autenticando...</h2>
            <p>Aguarde enquanto processamos seu login</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
