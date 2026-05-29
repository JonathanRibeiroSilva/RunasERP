import { FiPackage } from 'react-icons/fi';
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
}

const ProdutoCard: React.FC<ProdutoCardProps> = ({ produto, onClick }) => {
  return (
    <div className="produto-card" onClick={onClick}>
      <div className="produto-imagem">
        <FiPackage className="placeholder-icon" />
      </div>
      <div className="produto-info">
        <h3 className="produto-nome">{produto.nome}</h3>
        {produto.descricao && (
          <p className="produto-descricao">{produto.descricao}</p>
        )}
        <div className="produto-footer">
          <span className="produto-preco">Consulte</span>
          <button className="btn-ver-mais">Ver detalhes</button>
        </div>
      </div>
    </div>
  );
};

export default ProdutoCard;
