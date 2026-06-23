import './Configuracoes.scss';

const UsuariosPage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>👥 Gerenciar Usuários</h1>
        <p className="page-description">
          Adicione, edite e gerencie os usuários do sistema e suas permissões
        </p>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon">👥</div>
        <h3>Gerenciamento de Usuários</h3>
        <p>Controle o acesso ao sistema:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
          <li>Adicionar novos usuários</li>
          <li>Definir roles (Admin, Operador)</li>
          <li>Ativar/desativar usuários</li>
          <li>Gerenciar permissões</li>
        </ul>
        <p className="text-muted">Esta funcionalidade será implementada em breve.</p>
      </div>
    </div>
  );
};

export default UsuariosPage;
