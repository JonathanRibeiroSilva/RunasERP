import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/hooks/useAuth';
import { getErrorMessage } from '@/services/api/axios';
import { oauthService } from '@/services/auth/oauthService';
import { toast } from 'react-toastify';
import { FiMail, FiLock, FiLogIn, FiEye, FiEyeOff, FiAlertCircle } from 'react-icons/fi';
import { FcGoogle } from 'react-icons/fc';
import { SiMicrosoft } from 'react-icons/si';
import './LoginPage.scss';

// Schema de validação para login
const loginSchema = z.object({
  email: z.string().email('Email inválido').min(1, 'Email é obrigatório'),
  password: z.string().min(6, 'Senha deve ter no mínimo 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);

  // Form para login
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Limpar erro quando o usuário começa a digitar
  useEffect(() => {
    const subscription = loginForm.watch(() => {
      if (loginError) {
        setLoginError(null);
      }
    });

    return () => subscription.unsubscribe();
  }, [loginError, loginForm]);

  const onLoginSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setLoginError(null);
    console.log('[LoginPage] Tentando fazer login com:', data.email);
    try {
      await login(data.email, data.password);
      console.log('[LoginPage] Login bem-sucedido, redirecionando para dashboard');
      navigate('/dashboard');
    } catch (error) {
      console.log('[LoginPage] Erro ao fazer login:', error);
      const message = getErrorMessage(error);
      
      // Mensagens de erro mais específicas
      let errorMessage = message;
      
      if (message.toLowerCase().includes('invalid') || message.toLowerCase().includes('incorrect')) {
        errorMessage = 'Email ou senha incorretos. Verifique seus dados e tente novamente.';
      } else if (message.toLowerCase().includes('not found') || message.toLowerCase().includes('não encontrado')) {
        errorMessage = 'Usuário não encontrado. Verifique o email ou crie uma nova conta.';
      } else if (message.toLowerCase().includes('unauthorized') || message.toLowerCase().includes('não autorizado')) {
        errorMessage = 'Acesso negado. Verifique suas credenciais.';
      } else if (message.toLowerCase().includes('network') || message.toLowerCase().includes('conexão')) {
        errorMessage = 'Erro de conexão. Verifique sua internet e tente novamente.';
      }
      
      console.log('[LoginPage] Mensagem de erro:', errorMessage);
      setLoginError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthLogin = async (provider: 'google' | 'microsoft') => {
    try {
      setIsLoading(true);
      setLoginError(null);
      await oauthService.initiateOAuth(provider);
    } catch (error) {
      const message = getErrorMessage(error);
      setLoginError(message);
      toast.error(message);
      setIsLoading(false);
    }
  };

  // Verificar quais providers estão configurados
  const configuredProviders = oauthService.getConfiguredProviders();
  const hasOAuthProviders = configuredProviders.length > 0;

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-card">
          {/* Logo e Título */}
          <div className="login-header">
            <h1 className="login-title">Runas</h1>
            <p className="login-subtitle">Runas - Sistema de Gestão Empresarial</p>
          </div>

          {/* Mensagem de Erro */}
          {loginError && (
            <div className="alert alert-error">
              <FiAlertCircle className="alert-icon" />
              <div className="alert-content">
                <p className="alert-message">{loginError}</p>
              </div>
            </div>
          )}

          {/* Formulário de Login */}
          <form onSubmit={loginForm.handleSubmit(onLoginSubmit)} className="auth-form">
            {/* Email */}
            <div className="form-group">
              <label htmlFor="login-email" className="form-label">
                Email
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiMail />
                </span>
                <input
                  id="login-email"
                  type="email"
                  className={`form-control ${loginForm.formState.errors.email ? 'is-invalid' : ''}`}
                  placeholder="seu@email.com"
                  {...loginForm.register('email')}
                  disabled={isLoading}
                />
              </div>
              {loginForm.formState.errors.email && (
                <div className="invalid-feedback">{loginForm.formState.errors.email.message}</div>
              )}
            </div>

            {/* Senha */}
            <div className="form-group">
              <label htmlFor="login-password" className="form-label">
                Senha
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiLock />
                </span>
                <input
                  id="login-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`form-control ${loginForm.formState.errors.password ? 'is-invalid' : ''}`}
                  placeholder="••••••••"
                  {...loginForm.register('password')}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {loginForm.formState.errors.password && (
                <div className="invalid-feedback">{loginForm.formState.errors.password.message}</div>
              )}
            </div>

            {/* Botão Submit */}
            <button type="submit" className="btn btn-primary btn-auth" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" />
                  Entrando...
                </>
              ) : (
                <>
                  <FiLogIn />
                  Entrar
                </>
              )}
            </button>
          </form>

          {/* OAuth Buttons */}
          {hasOAuthProviders && (
            <>
              <div className="divider">
                <span>ou continue com</span>
              </div>

              <div className="oauth-buttons">
                {configuredProviders.includes('google') && (
                  <button
                    type="button"
                    className="btn-oauth btn-google"
                    onClick={() => handleOAuthLogin('google')}
                    disabled={isLoading}
                  >
                    <FcGoogle size={20} />
                    <span>Google</span>
                  </button>
                )}

                {configuredProviders.includes('microsoft') && (
                  <button
                    type="button"
                    className="btn-oauth btn-microsoft"
                    onClick={() => handleOAuthLogin('microsoft')}
                    disabled={isLoading}
                  >
                    <SiMicrosoft size={18} />
                    <span>Microsoft</span>
                  </button>
                )}
              </div>
            </>
          )}

          {/* Link para registro */}
          <div className="auth-link">
            <p>
              Não tem conta?{' '}
              <Link to="/register" className="link-primary">
                Criar conta
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
