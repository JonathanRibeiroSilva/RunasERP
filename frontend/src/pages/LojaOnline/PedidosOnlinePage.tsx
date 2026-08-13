import { FiShoppingBag } from 'react-icons/fi';
import './LojaOnline.scss';

const PedidosOnlinePage = () => {
  return (
    <div className="page-container">
      <div className="page-header">
        <h1><FiShoppingBag className="title-icon" /> Pedidos Online</h1>
        <p className="page-description">
          Gerencie os pedidos realizados através da loja online/catálogo público
        </p>
      </div>

      <div className="empty-state">
        <div className="empty-state-icon"><FiShoppingBag /></div>
        <h3>Pedidos Online</h3>
        <p>Aqui você verá todos os pedidos realizados pelos clientes através do catálogo público.</p>
        <p className="text-muted">Esta funcionalidade será implementada em breve.</p>
      </div>
    </div>
  );
};

export default PedidosOnlinePage;
