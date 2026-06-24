import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Toast } from '@/utils/toast';
import './AuthCallback.scss';

const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

const GoogleCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [processando, setProcessando] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    const processarCallback = async () => {
      const code = searchParams.get('code');
      const state = searchParams.get('state');
      const savedState = localStorage.getItem('oauth_state');
      const empresaSlug = localStorage.getItem('oauth_empresa_slug');

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
        });

        const { access_token, cliente } = response.data;

        // Salvar token
        localStorage.setItem('cliente_token', access_token);

        // Limpar dados OAuth
        localStorage.removeItem('oauth_state');
        localStorage.removeItem('oauth_empresa_slug');

        Toast.success(`Bem-vindo, ${cliente.nome}!`);

        // Redirecionar para checkout
        navigate(`/c/${empresaSlug}/checkout`);
      } catch (error: any) {
        const mensagem = error.response?.data?.detail || 'Erro ao processar login';
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
