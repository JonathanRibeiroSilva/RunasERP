import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { authService } from '@/services/auth/authService';
import { FiLock, FiEye, FiEyeOff, FiCheck, FiX } from 'react-icons/fi';
import './ResetPasswordPage.scss';

interface PasswordRule {
  label: string;
  test: (v: string) => boolean;
}

const passwordRules: PasswordRule[] = [
  { label: 'Mínimo 8 caracteres', test: (v) => v.length >= 8 },
  { label: 'Máximo 20 caracteres', test: (v) => v.length <= 20 },
  { label: 'Uma letra maiúscula', test: (v) => /[A-Z]/.test(v) },
  { label: 'Uma letra minúscula', test: (v) => /[a-z]/.test(v) },
  { label: 'Um número', test: (v) => /\d/.test(v) },
  { label: 'Um caractere especial (!@#$%...)', test: (v) => /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(v) },
];

const RunasLogo = () => (
  <svg viewBox="0 0 200 220" fill="none" xmlns="http://www.w3.org/2000/svg" className="runas-logo-svg">
    <polygon points="30,40 50,40 50,180 30,180" fill="url(#rspLogoGrad)" />
    <polygon points="50,40 95,40 110,60 95,80 50,80" fill="url(#rspLogoGrad)" />
    <polygon points="80,80 110,60 140,180 118,180" fill="url(#rspLogoGrad)" />
    <polygon points="30,40 80,10 88,24 38,54" fill="url(#rspLogoGrad)" opacity="0.85" />
    <polygon points="170,40 150,40 150,180 170,180" fill="url(#rspLogoGrad)" />
    <polygon points="150,40 105,40 90,60 105,80 150,80" fill="url(#rspLogoGrad)" />
    <polygon points="120,80 90,60 60,180 82,180" fill="url(#rspLogoGrad)" />
    <polygon points="170,40 120,10 112,24 162,54" fill="url(#rspLogoGrad)" opacity="0.85" />
    <defs>
      <linearGradient id="rspLogoGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#3b82f6" />
        <stop offset="100%" stopColor="#22d3ee" />
      </linearGradient>
    </defs>
  </svg>
);

const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';

  const [token, setToken] = useState(tokenFromUrl);
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');
  const [showNova, setShowNova] = useState(false);
  const [showConfirmar, setShowConfirmar] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const allRulesPass = passwordRules.every((r) => r.test(novaSenha));
  const senhasIguais = novaSenha === confirmarSenha && confirmarSenha.length > 0;
  const canSubmit = token.trim() && allRulesPass && senhasIguais;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setError('');
    setLoading(true);

    try {
      await authService.resetPassword(token.trim(), novaSenha);
      setSuccess(true);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError(detail || 'Erro ao resetar senha. Verifique o token e tente novamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="reset-password-page">
        <div className="reset-password-container">
          <div className="reset-password-card">
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

            <h2>Senha Redefinida!</h2>
            <p className="success-message">
              Sua senha foi atualizada com sucesso. Faça login com sua nova senha.
            </p>

            <button className="btn-primary" onClick={() => navigate('/login')}>
              Ir para Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="reset-password-page">
      <div className="reset-password-container">
        <div className="reset-password-card">
          <div className="logo-section">
            <RunasLogo />
            <h1 className="brand-name">RUNAS</h1>
          </div>

          <h2>Redefinir Senha</h2>
          <p className="subtitle">
            {tokenFromUrl
              ? 'Crie uma nova senha segura para sua conta.'
              : 'Cole o token recebido por email e crie uma nova senha.'}
          </p>

          {error && (
            <div className="alert alert-error">
              <FiX size={18} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* Token — só exibe se não veio pela URL */}
            {!tokenFromUrl && (
              <div className="form-group">
                <label htmlFor="token">Token de Recuperação</label>
                <input
                  type="text"
                  id="token"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="Cole o token recebido por email"
                  disabled={loading}
                  autoComplete="off"
                />
              </div>
            )}

            <div className="form-group">
              <label htmlFor="novaSenha">Nova Senha</label>
              <div className="input-wrapper">
                <FiLock className="input-icon" />
                <input
                  type={showNova ? 'text' : 'password'}
                  id="novaSenha"
                  value={novaSenha}
                  onChange={(e) => setNovaSenha(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="toggle-btn"
                  onClick={() => setShowNova(!showNova)}
                  tabIndex={-1}
                >
                  {showNova ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </div>

            {/* Regras de senha */}
            {novaSenha.length > 0 && (
              <div className="password-rules">
                {passwordRules.map((rule) => {
                  const ok = rule.test(novaSenha);
                  return (
                    <div key={rule.label} className={`rule ${ok ? 'ok' : 'fail'}`}>
                      {ok ? <FiCheck size={13} /> : <FiX size={13} />}
                      <span>{rule.label}</span>
                    </div>
                  );
                })}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="confirmarSenha">Confirmar Nova Senha</label>
              <div className="input-wrapper">
                <FiLock className="input-icon" />
                <input
                  type={showConfirmar ? 'text' : 'password'}
                  id="confirmarSenha"
                  value={confirmarSenha}
                  onChange={(e) => setConfirmarSenha(e.target.value)}
                  placeholder="••••••••"
                  disabled={loading}
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="toggle-btn"
                  onClick={() => setShowConfirmar(!showConfirmar)}
                  tabIndex={-1}
                >
                  {showConfirmar ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
              {confirmarSenha.length > 0 && !senhasIguais && (
                <span className="field-error">As senhas não coincidem</span>
              )}
            </div>

            <button
              type="submit"
              className="btn-submit"
              disabled={!canSubmit || loading}
            >
              {loading ? (
                <>
                  <span className="spinner" />
                  Redefinindo...
                </>
              ) : (
                'Redefinir Senha'
              )}
            </button>
          </form>

          <div className="footer-links">
            <Link to="/login">Voltar para Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordPage;
