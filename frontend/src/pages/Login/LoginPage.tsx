import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/services/api/axios';
import { Toast } from '@/utils/toast';
import { FiUser, FiLock, FiEye, FiEyeOff, FiShield } from 'react-icons/fi';
import logoImg from '@/img/logo1.png';
import './LoginPage.scss';

const loginSchema = z.object({
  email: z.string().email('Email inválido').min(1, 'Email é obrigatório'),
  password: z.string().min(6, 'Senha deve ter no mínimo 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

// Logo is imported via image now

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
      {/* Padrão de estrelas/fundo */}
      <div className="stars-bg"></div>

      <div className="login-card-premium">
        
        {/* Header - Logo e Título */}
        <div className="premium-header">
          <img src={logoImg} alt="Runas Logo" className="logo-img" />
          <h1>Bem-vindo ao <span className="brand-name">Runas</span></h1>
          <p>O conhecimento guia a gestão.</p>
        </div>



        {loginError && (
          <div className="login-error">
            <span>{loginError}</span>
          </div>
        )}

        <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="login-form" noValidate>
          <div className="field-group">
            <label htmlFor="email">Email</label>
            <div className="field-input">
              <input
                id="email"
                type="email"
                placeholder="seu@email.com..."
                autoComplete="email"
                {...loginForm.register('email')}
                disabled={isLoading}
                className={loginForm.formState.errors.email ? 'invalid' : ''}
              />
              <div className="input-glow-icon">
                <FiUser />
              </div>
            </div>
            {loginForm.formState.errors.email && (
              <span className="field-error">{loginForm.formState.errors.email.message}</span>
            )}
          </div>

          <div className="field-group">
            <label htmlFor="password">Senha</label>
            <div className="field-input">
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

          <button type="submit" className="btn-login" disabled={isLoading}>
            {isLoading ? <span className="spinner" /> : 'Login com email'}
          </button>
        </form>

      </div>
    </div>
  );
};

export default LoginPage;
