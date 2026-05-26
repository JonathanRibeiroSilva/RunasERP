import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { oauthService } from '@/services/auth/oauthService';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'react-toastify';
import { getErrorMessage } from '@/services/api/axios';
import './OAuthCallbackPage.scss';

const OAuthCallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setAuthUser, isAuthenticated, user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [shouldRedirect, setShouldRedirect] = useState(false);
  const processedRef = useRef(false); // Usar ref para persistir entre renderizações

  // useEffect para redirecionar quando autenticado
  useEffect(() => {
    if (shouldRedirect && isAuthenticated && user) {
      console.log('[OAuthCallback] useEffect detectou autenticação, redirecionando...');
      console.log('[OAuthCallback] isAuthenticated:', isAuthenticated);
      console.log('[OAuthCallback] user:', user);
      navigate('/dashboard', { replace: true });
    }
  }, [shouldRedirect, isAuthenticated, user, navigate]);

  useEffect(() => {
    const handleCallback = async () => {
      // Evitar múltiplas execuções (React StrictMode)
      if (processedRef.current) {
        console.log('[OAuthCallback] Já processado, ignorando execução duplicada');
        return;
      }
      
      console.log('[OAuthCallback] Primeira execução, processando callback...');
      processedRef.current = true;

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

        console.log('[OAuthCallback] Chamando backend com code e state...');
        // Processar callback
        const response = await oauthService.handleOAuthCallback(code, state);

        // Verificar se user existe na resposta
        if (!response.user) {
          throw new Error('Dados do usuário não retornados');
        }

        console.log('[OAuthCallback] Resposta recebida, usuário:', response.user);
        console.log('[OAuthCallback] Chamando setAuthUser...');
        // Atualizar contexto de autenticação com os dados do usuário
        setAuthUser(response.user);
        console.log('[OAuthCallback] setAuthUser executado');
        
        // Mostrar mensagem de sucesso
        toast.success(`Bem-vindo, ${response.user.nome}!`);

        console.log('[OAuthCallback] Ativando flag shouldRedirect');
        // Ativar flag para redirecionar via useEffect
        setShouldRedirect(true);
      } catch (err) {
        const message = getErrorMessage(err);
        console.error('[OAuth] Erro no callback:', message);
        setError(message);
        toast.error(`Erro no login: ${message}`);

        // Redirecionar para login após 3 segundos
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      }
    };

    handleCallback();
  }, [searchParams, setAuthUser, navigate]);

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
