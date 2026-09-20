import { FiPackage, FiShoppingCart } from 'react-icons/fi';
import './ProdutoCard.scss';

interface Produto {
  id: string;
  nome: string;
  descricao?: string;
  ativo: boolean;
  preco?: string | number;
  preco_promocional?: string | number | null;
  /** O preco que vale hoje, ja com a promocao resolvida pelo backend. */
  preco_efetivo?: string | number | null;
}

const formatarPreco = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);

interface ProdutoCardProps {
  produto: Produto;
  onClick: () => void;
  onAddToCart?: (e: React.MouseEvent) => void;
}

const ProdutoCard: React.FC<ProdutoCardProps> = ({ produto, onClick, onAddToCart }) => {
  // Quem decide se a promocao vale e o backend, em preco_efetivo: a regra
  // morava aqui e no carrinho ao mesmo tempo, e as duas se desencontraram —
  // a vitrine anunciava a promocao e o carrinho cobrava o preco cheio.
  // O fallback existe para a loja nao ficar sem preco se a API vier antiga.
  const precoBase = Number(produto.preco) || 0;
  const precoExibido = Number(produto.preco_efetivo) || precoBase;

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
        {precoExibido > 0 && (
          <div className="produto-preco" onClick={onClick}>
            {precoExibido < precoBase && (
              <span className="preco-antigo">{formatarPreco(precoBase)}</span>
            )}
            <span className="preco-atual">{formatarPreco(precoExibido)}</span>
          </div>
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
