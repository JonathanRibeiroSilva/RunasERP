import './Configuracoes.scss';

const IntegracoesPage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>🔌 Integrações</h1>
        <p className="page-description">
          Configure integrações com Mercado Pago, WhatsApp, e-mail e outros serviços
        </p>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon">🔌</div>
        <h3>Integrações Disponíveis</h3>
        <p>Conecte seu sistema com:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
          <li>Mercado Pago (pagamentos)</li>
          <li>Evolution API (WhatsApp)</li>
          <li>SMTP (e-mail transacional)</li>
          <li>OAuth (Google, Microsoft)</li>
        </ul>
        <p className="text-muted">Esta funcionalidade será implementada em breve.</p>
      </div>
    </div>
  );
};

export default IntegracoesPage;
