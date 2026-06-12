import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'react-toastify';
import { FiUser, FiMail, FiShield, FiLock, FiEye, FiEyeOff, FiSave } from 'react-icons/fi';
import './PerfilPage.scss';

const alterarSenhaSchema = z.object({
  senhaAtual: z.string().min(1, 'Senha atual é obrigatória'),
  novaSenha: z.string()
    .min(8, 'Nova senha deve ter no mínimo 8 caracteres')
    .max(20, 'Nova senha deve ter no máximo 20 caracteres')
    .regex(/[A-Z]/, 'Deve conter ao menos uma letra maiúscula')
    .regex(/[a-z]/, 'Deve conter ao menos uma letra minúscula')
    .regex(/[0-9]/, 'Deve conter ao menos um número')
    .regex(/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/, 'Deve conter ao menos um caractere especial'),
  confirmarSenha: z.string()
}).refine((data) => data.novaSenha === data.confirmarSenha, {
  message: "As senhas não coincidem",
  path: ["confirmarSenha"],
});

type AlterarSenhaFormData = z.infer<typeof alterarSenhaSchema>;

const PerfilPage = () => {
  const { user } = useAuth();
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const senhaForm = useForm<AlterarSenhaFormData>({
    resolver: zodResolver(alterarSenhaSchema),
  });

  const onSubmitSenha = async (data: AlterarSenhaFormData) => {
    setIsLoading(true);
    try {
      // TODO: Implementar chamada à API para alterar senha
      // await api.post('/auth/change-password', {
      //   current_password: data.senhaAtual,
      //   new_password: data.novaSenha
      // });
      
      toast.success('Senha alterada com sucesso!');
      senhaForm.reset();
    } catch (error) {
      toast.error('Erro ao alterar senha. Verifique sua senha atual.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="perfil-page">
        <div className="loading">Carregando...</div>
      </div>
    );
  }

  const roleLabels = {
    ADMIN: 'Administrador',
    OPERADOR: 'Operador'
  };

  return (
    <div className="perfil-page">
      <div className="page-header">
        <h1>Meu Perfil</h1>
        <p>Gerencie suas informações pessoais e configurações</p>
      </div>

      <div className="perfil-content">
        {/* Informações do Usuário */}
        <div className="perfil-card">
          <div className="card-header">
            <h2>Informações da Conta</h2>
            <div className="user-avatar">
              <FiUser size={32} />
            </div>
          </div>

          <div className="card-body">
            <div className="info-grid">
              <div className="info-item">
                <label>
                  <FiUser />
                  <span>Nome</span>
                </label>
                <p>{user.nome}</p>
              </div>

              <div className="info-item">
                <label>
                  <FiMail />
                  <span>Email</span>
                </label>
                <p>{user.email}</p>
              </div>

              <div className="info-item">
                <label>
                  <FiShield />
                  <span>Cargo</span>
                </label>
                <p className={`role-badge role-${user.role.toLowerCase()}`}>
                  {roleLabels[user.role]}
                </p>
              </div>

              <div className="info-item">
                <label>
                  <span>Status</span>
                </label>
                <p className="status-badge">
                  {user.ativo ? '✓ Ativo' : '✗ Inativo'}
                </p>
              </div>

              <div className="info-item full-width">
                <label>
                  <span>Membro desde</span>
                </label>
                <p>{new Date(user.criado_em).toLocaleDateString('pt-BR', {
                  day: '2-digit',
                  month: 'long',
                  year: 'numeric'
                })}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Alterar Senha */}
        <div className="perfil-card">
          <div className="card-header">
            <h2>Segurança</h2>
            <FiLock size={24} />
          </div>

          <div className="card-body">
            <form onSubmit={senhaForm.handleSubmit(onSubmitSenha)} className="senha-form">
              <div className="form-group">
                <label htmlFor="senhaAtual">Senha Atual</label>
                <div className="password-input">
                  <input
                    id="senhaAtual"
                    type={showCurrentPassword ? 'text' : 'password'}
                    placeholder="Digite sua senha atual"
                    {...senhaForm.register('senhaAtual')}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                    tabIndex={-1}
                  >
                    {showCurrentPassword ? <FiEyeOff /> : <FiEye />}
                  </button>
                </div>
                {senhaForm.formState.errors.senhaAtual && (
                  <span className="error-message">
                    {senhaForm.formState.errors.senhaAtual.message}
                  </span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="novaSenha">Nova Senha</label>
                <div className="password-input">
                  <input
                    id="novaSenha"
                    type={showNewPassword ? 'text' : 'password'}
                    placeholder="Digite sua nova senha"
                    {...senhaForm.register('novaSenha')}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    tabIndex={-1}
                  >
                    {showNewPassword ? <FiEyeOff /> : <FiEye />}
                  </button>
                </div>
                {senhaForm.formState.errors.novaSenha && (
                  <span className="error-message">
                    {senhaForm.formState.errors.novaSenha.message}
                  </span>
                )}
                <div className="password-requirements">
                  <small>A senha deve conter:</small>
                  <ul>
                    <li>Mínimo de 8 caracteres</li>
                    <li>Letras maiúsculas e minúsculas</li>
                    <li>Números</li>
                    <li>Caracteres especiais (!@#$%...)</li>
                  </ul>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="confirmarSenha">Confirmar Nova Senha</label>
                <div className="password-input">
                  <input
                    id="confirmarSenha"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirme sua nova senha"
                    {...senhaForm.register('confirmarSenha')}
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    className="toggle-password"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                  </button>
                </div>
                {senhaForm.formState.errors.confirmarSenha && (
                  <span className="error-message">
                    {senhaForm.formState.errors.confirmarSenha.message}
                  </span>
                )}
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isLoading}
                >
                  <FiSave />
                  {isLoading ? 'Salvando...' : 'Alterar Senha'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerfilPage;
