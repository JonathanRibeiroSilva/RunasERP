import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/services/api/axios';
import { Toast } from '@/utils/toast';
import { FiUser, FiLock, FiEye, FiEyeOff, FiShield } from 'react-icons/fi';
import './LoginPage.scss';

const loginSchema = z.object({
  email: z.string().email('Email inválido').min(1, 'Email é obrigatório'),
  password: z.string().min(6, 'Senha deve ter no mínimo 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

// Logo Runas em SVG inline
const RunasLogo = () => (
  <svg viewBox="0 0 200 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="runas-logo-svg">
    {/* Letra R esquerda */}
    <polygon points="30,40 50,40 50,180 30,180" fill="url(#logoGrad)" />
    <polygon points="50,40 95,40 110,60 95,80 50,80" fill="url(#logoGrad)" />
    <polygon points="80,80 110,60 140,180 118,180" fill="url(#logoGrad)" />
    {/* Diagonal superior esquerda */}
    <polygon points="30,40 80,10 88,24 38,54" fill="url(#logoGrad)" opacity="0.85" />

    {/* Letra R direita (espelhada) */}
    <polygon points="170,40 150,40 150,180 170,180" fill="url(#logoGrad)" />
    <polygon points="150,40 105,40 90,60 105,80 150,80" fill="url(#logoGrad)" />
    <polygon points="120,80 90,60 60,180 82,180" fill="url(#logoGrad)" />
    {/* Diagonal superior direita */}
    <polygon points="170,40 120,10 112,24 162,54" fill="url(#logoGrad)" opacity="0.85" />

    <defs>
      <linearGradient id="logoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3b82f6" />
        <stop offset="100%" stopColor="#22d3ee" />
      </linearGradient>
    </defs>
  </svg>
);

const features = [
  {
    icon: '📊',
    title: 'Análise em Tempo Real',
    desc: 'Monitore métricas e KPIs instantaneamente',
  },
  {
    icon: '🔒',
    title: 'Segurança Avançada',
    desc: 'Proteção multicamadas e auditoria completa',
  },
  {
    icon: '💡',
    title: 'Inteligência de Dados',
    desc: 'Insights e relatórios automatizados',
  },
];

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    const subscription = loginForm.watch(() => {
      if (loginError) setLoginError(null);
    });
    return () => subscription.unsubscribe();
  }, [loginError, loginForm]);

  const onLoginSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setLoginError(null);
    
    const toastId = Toast.loading('Entrando...');
    
    try {
      await login(data.email, data.password);
      Toast.update(toastId, 'success', 'Login realizado com sucesso!');
      navigate('/dashboard');
    } catch (error) {
      Toast.dismiss(toastId);
      
      const message = getErrorMessage(error);
      let errorMessage = message;
      if (message.toLowerCase().includes('invalid') || message.toLowerCase().includes('incorrect')) {
        errorMessage = 'Email ou senha incorretos.';
      } else if (message.toLowerCase().includes('not found')) {
        errorMessage = 'Usuário não encontrado.';
      } else if (message.toLowerCase().includes('network')) {
        errorMessage = 'Erro de conexão. Verifique sua internet.';
      }
      setLoginError(errorMessage);
      Toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Painel esquerdo — apresentação */}
      <div className="login-left">
        <div className="left-content">
          <div className="brand">
            <RunasLogo />
            <span className="brand-name">RUNAS</span>
          </div>

          <div className="left-text">
            <h2> Sistema de Gestão Comercial</h2>
          </div>

          <div className="features">
            {features.map((f) => (
              <div className="feature-item" key={f.title}>
                <div className="feature-icon">{f.icon}</div>
                <div className="feature-text">
                  <strong>{f.title}</strong>
                  <span>{f.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Efeito de fundo decorativo */}
        <div className="left-glow" />
      </div>

      {/* Painel direito — formulário */}
      <div className="login-right">
        <div className="login-form-wrapper">
          <div className="form-header">
            <h1>Seja Bem-vindo</h1>
            <p>Faça login para acessar sua plataforma</p>
          </div>

          {loginError && (
            <div className="login-error">
              <span>{loginError}</span>
            </div>
          )}

          <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="login-form" noValidate>
            <div className="field-group">
              <label htmlFor="email">Usuário</label>
              <div className="field-input">
                <FiUser className="field-icon" />
                <input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  autoComplete="email"
                  {...loginForm.register('email')}
                  disabled={isLoading}
                  className={loginForm.formState.errors.email ? 'invalid' : ''}
                />
              </div>
              {loginForm.formState.errors.email && (
                <span className="field-error">{loginForm.formState.errors.email.message}</span>
              )}
            </div>

            <div className="field-group">
              <label htmlFor="password">Senha</label>
              <div className="field-input">
                <FiLock className="field-icon" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  {...loginForm.register('password')}
                  disabled={isLoading}
                  className={loginForm.formState.errors.password ? 'invalid' : ''}
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {loginForm.formState.errors.password && (
                <span className="field-error">{loginForm.formState.errors.password.message}</span>
              )}
            </div>

            <div className="form-options">
              <label className="remember-me">
                <input type="checkbox" />
                <span>Manter conectado</span>
              </label>
              <Link to="/forgot-password" className="forgot-link">Esqueceu a senha?</Link>
            </div>

            <button type="submit" className="btn-login" disabled={isLoading}>
              {isLoading ? (
                <span className="spinner" />
              ) : null}
              {isLoading ? 'Entrando...' : 'Acessar Plataforma'}
            </button>
          </form>

          <div className="form-footer">
            <div className="ssl-badge">
              <FiShield />
              <span>CONEXÃO SEGURA SSL</span>
            </div>
            <p className="copyright">© 2025 Runas. Todos os direitos reservados.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
