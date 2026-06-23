import { FiPackage, FiShoppingCart } from 'react-icons/fi';
import './ProdutoCard.scss';

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  ativo: boolean;
}

interface ProdutoCardProps {
  produto: Produto;
  onClick: () => void;
  onAddToCart?: (e: React.MouseEvent) => void;
}

const ProdutoCard: React.FC<ProdutoCardProps> = ({ produto, onClick, onAddToCart }) => {
  const handleAddToCart = (e: React.MouseEvent) => {
    e.stopPropagation(); // Evita abrir detalhes ao clicar em adicionar
    if (onAddToCart) onAddToCart(e);
  };

  return (
    <div className="produto-card">
      <div className="produto-imagem" onClick={onClick}>
        <FiPackage className="placeholder-icon" />
      </div>
      <div className="produto-info">
        <h3 className="produto-nome" onClick={onClick}>{produto.nome}</h3>
        {produto.descricao && (
          <p className="produto-descricao" onClick={onClick}>{produto.descricao}</p>
        )}
        <div className="produto-footer">
          <button className="btn-ver-detalhes" onClick={onClick}>
            Ver detalhes
          </button>
          <button 
            className="btn-add-carrinho" 
            onClick={handleAddToCart}
            title="Adicionar ao carrinho"
          >
            <FiShoppingCart />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProdutoCard;
