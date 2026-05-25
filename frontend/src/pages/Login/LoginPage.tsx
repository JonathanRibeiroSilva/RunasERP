import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@/contexts/AuthContext';
import { getErrorMessage } from '@/services/api/axios';
import { oauthService } from '@/services/auth/oauthService';
import { toast } from 'react-toastify';
import { FiMail, FiLock, FiLogIn } from 'react-icons/fi';
import { FcGoogle } from 'react-icons/fc';
import { SiMicrosoft } from 'react-icons/si';
import './LoginPage.scss';

// Schema de validação
const loginSchema = z.object({
  email: z.string().email('Email inválido').min(1, 'Email é obrigatório'),
  password: z.string().min(6, 'Senha deve ter no mínimo 6 caracteres'),
});

type LoginFormData = z.infer<typeof loginSchema>;

const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      await login(data.email, data.password);
      navigate('/dashboard');
    } catch (error) {
      const message = getErrorMessage(error);
      toast.error(message || 'Erro ao fazer login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthLogin = (provider: 'google' | 'microsoft') => {
    try {
      oauthService.initiateOAuth(provider);
    } catch (error) {
      const message = getErrorMessage(error);
      toast.error(message);
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
            <h1 className="login-title">ERP Runas</h1>
            <p className="login-subtitle">Sistema de Gestão Empresarial</p>
          </div>

          {/* Formulário */}
          <form onSubmit={handleSubmit(onSubmit)} className="login-form">
            {/* Email */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiMail />
                </span>
                <input
                  id="email"
                  type="email"
                  className={`form-control ${errors.email ? 'is-invalid' : ''}`}
                  placeholder="seu@email.com"
                  {...register('email')}
                  disabled={isLoading}
                />
              </div>
              {errors.email && <div className="invalid-feedback">{errors.email.message}</div>}
            </div>

            {/* Senha */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Senha
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiLock />
                </span>
                <input
                  id="password"
                  type="password"
                  className={`form-control ${errors.password ? 'is-invalid' : ''}`}
                  placeholder="••••••••"
                  {...register('password')}
                  disabled={isLoading}
                />
              </div>
              {errors.password && (
                <div className="invalid-feedback">{errors.password.message}</div>
              )}
            </div>

            {/* Botão Submit */}
            <button type="submit" className="btn btn-primary btn-login" disabled={isLoading}>
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

          {/* Credenciais de teste */}
          <div className="login-footer">
            <p className="text-muted">
              <small>
                <strong>Credenciais de teste:</strong>
                <br />
                Email: admin@runas.com
                <br />
                Senha: Admin@123
              </small>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
