import './LojaOnline.scss';

const ConfiguracoesLojaPage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1>⚙️ Configurações da Loja</h1>
        <p className="page-description">
          Configure aparência, textos, formas de pagamento e outras opções da loja online
        </p>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon">⚙️</div>
        <h3>Configurações da Loja Online</h3>
        <p>Personalize sua loja online:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
          <li>Cores e logotipo</li>
          <li>Textos de apresentação</li>
          <li>WhatsApp de contato</li>
          <li>Formas de pagamento</li>
          <li>Política de entrega</li>
        </ul>
        <p className="text-muted">Esta funcionalidade será implementada em breve.</p>
      </div>
    </div>
  );
};

export default ConfiguracoesLojaPage;
