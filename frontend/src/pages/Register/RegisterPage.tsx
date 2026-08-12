import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { authService } from '@/services/auth/authService';
import { getErrorMessage } from '@/services/api/axios';
import { toast } from 'react-toastify';
import { FiMail, FiLock, FiUserPlus, FiUser, FiEye, FiEyeOff } from 'react-icons/fi';
import './RegisterPage.scss';

// Schema de validação para registro
const registerSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres').max(255, 'Nome muito longo'),
  email: z.string().email('Email inválido').min(1, 'Email é obrigatório'),
  password: z
    .string()
    .min(8, 'Senha deve ter no mínimo 8 caracteres')
    .max(20, 'Senha deve ter no máximo 20 caracteres')
    .regex(/[A-Z]/, 'Senha deve conter ao menos uma letra maiúscula')
    .regex(/[a-z]/, 'Senha deve conter ao menos uma letra minúscula')
    .regex(/[0-9]/, 'Senha deve conter ao menos um número')
    .regex(/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/, 'Senha deve conter ao menos um caractere especial'),
  confirmPassword: z.string().min(1, 'Confirmação de senha é obrigatória'),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Senhas não coincidem',
  path: ['confirmPassword'],
});

type RegisterFormData = z.infer<typeof registerSchema>;

const RegisterPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Form para registro
  const registerForm = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  const password = registerForm.watch('password');

  const onRegisterSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    try {
      await authService.register({
        nome: data.nome,
        email: data.email,
        senha: data.password,
      });
      
      toast.success('Conta criada com sucesso! Faça login para continuar.');
      navigate('/login', { state: { email: data.email } });
    } catch (error) {
      const message = getErrorMessage(error);
      toast.error(message || 'Erro ao criar conta');
    } finally {
      setIsLoading(false);
    }
  };

  // Validações em tempo real para feedback visual
  const passwordValidations = {
    length: password && password.length >= 8 && password.length <= 20,
    uppercase: password && /[A-Z]/.test(password),
    lowercase: password && /[a-z]/.test(password),
    number: password && /[0-9]/.test(password),
    special: password && /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password),
  };

  return (
    <div className="register-page">
      <div className="register-container">
        <div className="register-card">
          {/* Logo e Título */}
          <div className="register-header">
            <h1 className="register-title">Criar Conta</h1>
            <p className="register-subtitle">Runas - Sistema de Gestão Comercial</p>
          </div>

          {/* Formulário de Registro */}
          <form onSubmit={registerForm.handleSubmit(onRegisterSubmit)} className="auth-form">
            {/* Nome */}
            <div className="form-group">
              <label htmlFor="register-nome" className="form-label">
                Nome Completo
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiUser />
                </span>
                <input
                  id="register-nome"
                  type="text"
                  className={`form-control ${registerForm.formState.errors.nome ? 'is-invalid' : ''}`}
                  placeholder="Seu nome completo"
                  {...registerForm.register('nome')}
                  disabled={isLoading}
                />
              </div>
              {registerForm.formState.errors.nome && (
                <div className="invalid-feedback">{registerForm.formState.errors.nome.message}</div>
              )}
            </div>

            {/* Email */}
            <div className="form-group">
              <label htmlFor="register-email" className="form-label">
                Email
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiMail />
                </span>
                <input
                  id="register-email"
                  type="email"
                  className={`form-control ${registerForm.formState.errors.email ? 'is-invalid' : ''}`}
                  placeholder="seu@email.com"
                  {...registerForm.register('email')}
                  disabled={isLoading}
                />
              </div>
              {registerForm.formState.errors.email && (
                <div className="invalid-feedback">{registerForm.formState.errors.email.message}</div>
              )}
            </div>

            {/* Senha */}
            <div className="form-group">
              <label htmlFor="register-password" className="form-label">
                Senha
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiLock />
                </span>
                <input
                  id="register-password"
                  type={showPassword ? 'text' : 'password'}
                  className={`form-control ${registerForm.formState.errors.password ? 'is-invalid' : ''}`}
                  placeholder="••••••••"
                  {...registerForm.register('password')}
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
              {registerForm.formState.errors.password && (
                <div className="invalid-feedback">{registerForm.formState.errors.password.message}</div>
              )}
              
              {/* Indicadores de força da senha */}
              {password && (
                <div className="password-strength">
                  <div className="strength-indicators">
                    <div className={`indicator ${passwordValidations.length ? 'valid' : 'invalid'}`}>
                      8-20 caracteres
                    </div>
                    <div className={`indicator ${passwordValidations.uppercase ? 'valid' : 'invalid'}`}>
                      Maiúscula
                    </div>
                    <div className={`indicator ${passwordValidations.lowercase ? 'valid' : 'invalid'}`}>
                      Minúscula
                    </div>
                    <div className={`indicator ${passwordValidations.number ? 'valid' : 'invalid'}`}>
                      Número
                    </div>
                    <div className={`indicator ${passwordValidations.special ? 'valid' : 'invalid'}`}>
                      Especial
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Confirmar Senha */}
            <div className="form-group">
              <label htmlFor="register-confirmPassword" className="form-label">
                Confirmar Senha
              </label>
              <div className="input-group">
                <span className="input-icon">
                  <FiLock />
                </span>
                <input
                  id="register-confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  className={`form-control ${registerForm.formState.errors.confirmPassword ? 'is-invalid' : ''}`}
                  placeholder="••••••••"
                  {...registerForm.register('confirmPassword')}
                  disabled={isLoading}
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={isLoading}
                >
                  {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {registerForm.formState.errors.confirmPassword && (
                <div className="invalid-feedback">{registerForm.formState.errors.confirmPassword.message}</div>
              )}
            </div>

            {/* Botão Submit */}
            <button type="submit" className="btn btn-primary btn-auth" disabled={isLoading}>
              {isLoading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" />
                  Criando conta...
                </>
              ) : (
                <>
                  <FiUserPlus />
                  Criar Conta
                </>
              )}
            </button>
          </form>

          {/* Link para login */}
          <div className="auth-link">
            <p>
              Já tem conta?{' '}
              <Link to="/login" className="link-primary">
                Fazer login
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
