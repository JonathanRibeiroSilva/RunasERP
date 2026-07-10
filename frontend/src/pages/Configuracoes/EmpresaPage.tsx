import { FiBriefcase } from 'react-icons/fi';
import './Configuracoes.scss';

const EmpresaPage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1><FiBriefcase className="title-icon" /> Dados da Empresa</h1>
        <p className="page-description">
          Configure os dados cadastrais, endereço e informações fiscais da empresa
        </p>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon"><FiBriefcase /></div>
        <h3>Configurações da Empresa</h3>
        <p>Gerencie as informações da sua empresa:</p>
        <ul style={{ textAlign: 'left', maxWidth: '400px', margin: '0 auto' }}>
          <li>Razão Social e Nome Fantasia</li>
          <li>CNPJ e Inscrições</li>
          <li>Endereço e contatos</li>
          <li>Regime tributário</li>
          <li>Plano e limites</li>
        </ul>
        <p className="text-muted">Esta funcionalidade será implementada em breve.</p>
      </div>
    </div>
  );
};

export default EmpresaPage;
