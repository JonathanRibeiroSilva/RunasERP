import { useState } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services/auth/authService';
import { FiArrowLeft } from 'react-icons/fi';
import './ForgotPasswordPage.scss';

const RunasLogo = () => (
  <svg viewBox="0 0 200 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="runas-logo-svg">
    <polygon points="30,40 50,40 50,180 30,180" fill="url(#fpLogoGrad)" />
    <polygon points="50,40 95,40 110,60 95,80 50,80" fill="url(#fpLogoGrad)" />
    <polygon points="80,80 110,60 140,180 118,180" fill="url(#fpLogoGrad)" />
    <polygon points="30,40 80,10 88,24 38,54" fill="url(#fpLogoGrad)" opacity="0.85" />
    <polygon points="170,40 150,40 150,180 170,180" fill="url(#fpLogoGrad)" />
    <polygon points="150,40 105,40 90,60 105,80 150,80" fill="url(#fpLogoGrad)" />
    <polygon points="120,80 90,60 60,180 82,180" fill="url(#fpLogoGrad)" />
    <polygon points="170,40 120,10 112,24 162,54" fill="url(#fpLogoGrad)" opacity="0.85" />
    <defs>
      <linearGradient id="fpLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3b82f6" />
        <stop offset="100%" stopColor="#22d3ee" />
      </linearGradient>
    </defs>
  </svg>
);

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setError('');
    setLoading(true);

    try {
      await authService.forgotPassword(email);
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao solicitar reset de senha. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="forgot-password-page">
        <div className="forgot-password-container">
          <div className="forgot-password-card">
            <div className="logo-section">
              <RunasLogo />
              <h1 className="brand-name">RUNAS</h1>
            </div>

            <div className="success-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="#10B981" strokeWidth="2" />
                <path d="M8 12L11 15L16 9" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>

            <h2>Email Enviado!</h2>
            <p className="success-message">
              Se o email <strong>{email}</strong> estiver cadastrado, você receberá instruções para resetar sua senha.
            </p>
            <p className="info-text">
              Verifique sua caixa de entrada e spam. O link expira em 1 hora.
            </p>

            <Link to="/login" className="btn-back">
              <FiArrowLeft />
              Voltar para Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="forgot-password-page">
      <div className="forgot-password-container">
        <div className="forgot-password-card">
          <div className="logo-section">
            <RunasLogo />
            <h1 className="brand-name">RUNAS</h1>
          </div>

          <h2>Esqueceu sua senha?</h2>
          <p className="subtitle">
            Digite seu email e enviaremos instruções para resetar sua senha.
          </p>

          {error && (
            <div className="alert alert-error">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
                <path d="M12 8V12M12 16H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              </svg>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="seu@email.com"
                required
                disabled={loading}
                autoFocus
                autoComplete="email"
              />
            </div>

            <button type="submit" className="btn-submit" disabled={loading || !email}>
              {loading ? (
                <>
                  <span className="spinner" />
                  Enviando...
                </>
              ) : (
                'Enviar Instruções'
              )}
            </button>
          </form>

          <div className="footer-links">
            <Link to="/login">
              <FiArrowLeft style={{ verticalAlign: 'middle', marginRight: 4 }} />
              Voltar para Login
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
