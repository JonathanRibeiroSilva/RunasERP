import { useState } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { FiMail, FiLock, FiArrowLeft, FiUser, FiPhone, FiFileText } from 'react-icons/fi';
import { FaGoogle, FaMicrosoft } from 'react-icons/fa';
import axios from 'axios';
import { toast } from 'react-toastify';
import './ClienteLoginPage.scss';

const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

const ClienteLoginPage = () => {
  const navigate = useNavigate();
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const location = useLocation();
  
  const [modo, setModo] = useState<'login' | 'cadastro'>('login');
  const [loading, setLoading] = useState(false);
  
  // Formulário de Login
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  
  // Formulário de Cadastro
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [cpf, setCpf] = useState('');
  const [emailCadastro, setEmailCadastro] = useState('');
  const [senhaCadastro, setSenhaCadastro] = useState('');
  const [confirmarSenha, setConfirmarSenha] = useState('');

  // URL de retorno após login
  const from = (location.state as any)?.from || `/c/${empresaSlug}/minha-conta/pedidos`;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !senha) {
      toast.error('Preencha e-mail e senha');
      return;
    }

    try {
      setLoading(true);
      
      // Montar FormData para OAuth2PasswordRequestForm
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', senha);
      
      await apiPublica.post('/auth/cliente/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      
      toast.success('Login realizado com sucesso!');
      
      // Redirecionar para página de origem ou área do cliente
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Erro no login:', error);
      toast.error(error.response?.data?.detail || 'E-mail ou senha incorretos');
    } finally {
      setLoading(false);
    }
  };

  const handleCadastro = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validações
    if (!nome || !emailCadastro || !telefone || !senhaCadastro) {
      toast.error('Preencha todos os campos obrigatórios');
      return;
    }
    
    if (senhaCadastro !== confirmarSenha) {
      toast.error('As senhas não coincidem');
      return;
    }
    
    if (senhaCadastro.length < 6) {
      toast.error('A senha deve ter no mínimo 6 caracteres');
      return;
    }

    try {
      setLoading(true);
      
      // Buscar empresa_id
      const empresaRes = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaRes.data.id;
      
      await apiPublica.post('/auth/cliente/register', {
        nome,
        email: emailCadastro,
        telefone: telefone.replace(/\D/g, ''), // Remover formatação
        cpf: cpf ? cpf.replace(/\D/g, '') : undefined,
        senha: senhaCadastro,
        empresa_id,
      });
      
      toast.success('Cadastro realizado com sucesso!');
      
      // Redirecionar para página de origem ou área do cliente
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Erro no cadastro:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar conta');
    } finally {
      setLoading(false);
    }
  };

  const handleOAuthGoogle = async () => {
    try {
      setLoading(true);
      
      // Buscar empresa_id
      const empresaRes = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaRes.data.id;
      
      const redirectUri = `${window.location.origin}/auth/callback/google`;
      
      const response = await apiPublica.post('/auth/cliente/oauth/google/init', {
        redirect_uri: redirectUri,
        empresa_id,
      });
      
      // Salvar URL de retorno no sessionStorage
      sessionStorage.setItem('oauth_return_url', from);
      
      // Redirecionar para Google
      window.location.href = response.data.auth_url;
    } catch (error: any) {
      console.error('Erro OAuth Google:', error);
      toast.error('Erro ao iniciar login com Google');
      setLoading(false);
    }
  };

  const handleOAuthMicrosoft = async () => {
    try {
      setLoading(true);
      
      // Buscar empresa_id
      const empresaRes = await apiPublica.get(`/empresas/publico/${empresaSlug}`);
      const empresa_id = empresaRes.data.id;
      
      const redirectUri = `${window.location.origin}/auth/callback/microsoft`;
      
      const response = await apiPublica.post('/auth/cliente/oauth/microsoft/init', {
        redirect_uri: redirectUri,
        empresa_id,
      });
      
      // Salvar URL de retorno no sessionStorage
      sessionStorage.setItem('oauth_return_url', from);
      
      // Redirecionar para Microsoft
      window.location.href = response.data.auth_url;
    } catch (error: any) {
      console.error('Erro OAuth Microsoft:', error);
      toast.error('Erro ao iniciar login com Microsoft');
      setLoading(false);
    }
  };

  const formatarTelefone = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 10) {
      return numbers.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    }
    return numbers.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
  };

  const formatarCPF = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
  };

  return (
    <div className="cliente-login-page">
      <div className="login-container">
        {/* Header */}
        <div className="login-header">
          <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}`)}>
            <FiArrowLeft /> Voltar para loja
          </button>
          <h1>Bem-vindo de volta! 👋</h1>
          <p>Acesse sua conta para continuar</p>
        </div>

        {/* Abas */}
        <div className="tabs">
          <button
            className={`tab ${modo === 'login' ? 'ativo' : ''}`}
            onClick={() => setModo('login')}
          >
            Entrar
          </button>
          <button
            className={`tab ${modo === 'cadastro' ? 'ativo' : ''}`}
            onClick={() => setModo('cadastro')}
          >
            Criar Conta
          </button>
        </div>

        {/* OAuth Buttons */}
        <div className="oauth-section">
          <p className="oauth-label">Acesse com suas contas existentes</p>
          <div className="oauth-buttons">
            <button
              className="btn-oauth google"
              onClick={handleOAuthGoogle}
              disabled={loading}
            >
              <FaGoogle />
              Google
            </button>
            <button
              className="btn-oauth microsoft"
              onClick={handleOAuthMicrosoft}
              disabled={loading}
            >
              <FaMicrosoft />
              Microsoft
            </button>
          </div>
          <div className="divider">
            <span>ou use e-mail e senha</span>
          </div>
        </div>

        {/* Formulário de Login */}
        {modo === 'login' && (
          <form className="login-form" onSubmit={handleLogin}>
            <div className="form-group">
              <label>
                <FiMail />
                E-mail *
              </label>
              <input
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiLock />
                Senha *
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>
        )}

        {/* Formulário de Cadastro */}
        {modo === 'cadastro' && (
          <form className="login-form" onSubmit={handleCadastro}>
            <div className="form-group">
              <label>
                <FiUser />
                Nome Completo *
              </label>
              <input
                type="text"
                placeholder="Seu nome completo"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiMail />
                E-mail *
              </label>
              <input
                type="email"
                placeholder="seu@email.com"
                value={emailCadastro}
                onChange={(e) => setEmailCadastro(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiPhone />
                Telefone *
              </label>
              <input
                type="tel"
                placeholder="(11) 99999-9999"
                value={telefone}
                onChange={(e) => setTelefone(formatarTelefone(e.target.value))}
                maxLength={15}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiFileText />
                CPF (opcional)
              </label>
              <input
                type="text"
                placeholder="000.000.000-00"
                value={cpf}
                onChange={(e) => setCpf(formatarCPF(e.target.value))}
                maxLength={14}
              />
            </div>

            <div className="form-group">
              <label>
                <FiLock />
                Senha *
              </label>
              <input
                type="password"
                placeholder="Mínimo 6 caracteres"
                value={senhaCadastro}
                onChange={(e) => setSenhaCadastro(e.target.value)}
                minLength={6}
                required
              />
            </div>

            <div className="form-group">
              <label>
                <FiLock />
                Confirmar Senha *
              </label>
              <input
                type="password"
                placeholder="Digite a senha novamente"
                value={confirmarSenha}
                onChange={(e) => setConfirmarSenha(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Criando conta...' : 'Criar Conta'}
            </button>
          </form>
        )}
      </div>

      {/* Footer */}
      <footer className="login-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default ClienteLoginPage;
