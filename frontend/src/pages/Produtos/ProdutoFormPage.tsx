import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQueryClient } from '@tanstack/react-query';
import { FiX, FiEdit2, FiPackage } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api, getErrorMessage } from '@/services/api/axios';
import { estoqueApi } from '@/services/api/estoqueApi';
import { useAuth } from '@/hooks/useAuth';
import { UNIDADES_MEDIDA, type UnidadeMedida } from '@/types/produtos';
import './ProdutoFormPage.scss';

const CODIGOS_UNIDADE = UNIDADES_MEDIDA.map((unidade) => unidade.codigo) as [
  UnidadeMedida,
  ...UnidadeMedida[],
];

const quantidadeOpcional = (mensagem: string) =>
  z.preprocess(
    (valor) => (valor === '' || valor === undefined || valor === null ? 0 : valor),
    z.coerce.number().min(0, mensagem)
  );

// Schema de validação
const produtoSchema = z
  .object({
    nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
    categoria_id: z.string().uuid('Categoria inválida'),
    descricao: z.string().optional().or(z.literal('')),
    preco: z.coerce.number().min(0, 'Preço não pode ser negativo'),
    custo: z.coerce.number().min(0, 'Custo não pode ser negativo'),
    preco_promocional: z.preprocess(
      (valor) => (valor === '' || valor === null ? undefined : valor),
      z.coerce.number().positive('Preço promocional deve ser maior que zero').optional()
    ),
    unidade_medida: z.enum(CODIGOS_UNIDADE),
    ativo: z.boolean(),
    estoque_inicial: quantidadeOpcional('Quantidade não pode ser negativa'),
    estoque_minimo: quantidadeOpcional('Estoque mínimo não pode ser negativo'),
  })
  .refine((dados) => dados.preco >= dados.custo, {
    message: 'Preço de venda não pode ser menor que o custo',
    path: ['preco'],
  })
  .refine((dados) => dados.ativo || dados.estoque_inicial === 0, {
    message: 'Produto inativo não pode receber estoque inicial',
    path: ['estoque_inicial'],
  });

// zod 4 splits input from output: coerce/preprocess take unknown in, give number out.
type ProdutoFormInput = z.input<typeof produtoSchema>;
type ProdutoFormData = z.output<typeof produtoSchema>;

interface Categoria {
  id: string;
  nome: string;
}

interface ProdutoFormPageProps {
  isModal?: boolean;
  produtoId?: string | null;
  onClose?: () => void;
}

const ProdutoFormPage: React.FC<ProdutoFormPageProps> = ({ isModal, produtoId: modalProdutoId, onClose }) => {
  const navigate = useNavigate();
  const { id: routeId } = useParams<{ id: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const id = isModal ? (modalProdutoId ?? undefined) : routeId;
  const [loading, setLoading] = useState(!!id);
  const [submitting, setSubmitting] = useState(false);
  const [categorias, setCategorias] = useState<Categoria[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ProdutoFormInput, unknown, ProdutoFormData>({
    resolver: zodResolver(produtoSchema),
    defaultValues: { unidade_medida: 'UN', ativo: true, estoque_inicial: 0, estoque_minimo: 0 },
  });

  const produtoAtivo = watch('ativo');

  useEffect(() => {
    carregarCategorias();
    if (id) {
      carregarProduto();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const carregarCategorias = async () => {
    try {
      const response = await api.get('/categorias?limit=100');
      setCategorias(response.data.items || []);
    } catch (error) {
      toast.error('Erro ao carregar categorias');
      console.error(error);
    }
  };

  const carregarProduto = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/produtos/${id}`);
      reset(response.data);
    } catch (error) {
      toast.error('Erro ao carregar produto');
      console.error(error);
      handleClose();
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (isModal && onClose) onClose();
    else navigate('/produtos');
  };

  /**
   * Bootstrap do estoque inicial: orquestra o serviço de Estoque via API existente
   * (nunca cria linha de estoque por dentro do serviço de Produtos).
   * - quantidade > 0 → POST /estoque/entrada (cria a linha lazily + movimentação auditada)
   * - quantidade = 0 e mínimo > 0 → POST /estoque (linha zerada só para configurar o mínimo)
   */
  const lancarEstoqueInicial = async (produtoId: string, data: ProdutoFormData) => {
    if (data.estoque_inicial > 0) {
      const estoque = await estoqueApi.entrada({
        empresa_id: user!.empresa_id,
        produto_id: produtoId,
        quantidade: data.estoque_inicial,
        custo_unitario: data.custo > 0 ? data.custo : undefined,
        motivo: 'Cadastro Inicial',
        documento: 'Cadastro do Produto',
      });
      if (data.estoque_minimo > 0) {
        await estoqueApi.atualizar(estoque.id, { estoque_minimo: data.estoque_minimo });
      }
      return;
    }
    if (data.estoque_minimo > 0) {
      await estoqueApi.criar({
        empresa_id: user!.empresa_id,
        produto_id: produtoId,
        quantidade: 0,
        estoque_minimo: data.estoque_minimo,
      });
    }
  };

  const onSubmit = async (data: ProdutoFormData) => {
    // Payload do serviço de Produtos — estoque_inicial/estoque_minimo pertencem ao Estoque.
    const dadosProduto = {
      nome: data.nome,
      categoria_id: data.categoria_id,
      descricao: data.descricao,
      preco: data.preco,
      custo: data.custo,
      preco_promocional: data.preco_promocional,
      unidade_medida: data.unidade_medida,
      ativo: data.ativo,
    };

    try {
      setSubmitting(true);

      if (id) {
        // Editar
        await api.put(`/produtos/${id}`, dadosProduto);
        toast.success('Produto atualizado com sucesso');
      } else {
        // Criar produto e, em seguida, orquestrar o estoque inicial
        const criado = await api.post('/produtos', { ...dadosProduto, empresa_id: user!.empresa_id });
        try {
          await lancarEstoqueInicial(criado.data.id, data);
          toast.success('Produto criado com sucesso');
        } catch (erroEstoque) {
          toast.warn(
            `Produto criado, mas o estoque inicial não pôde ser lançado: ${getErrorMessage(erroEstoque)}. Use a tela de Estoque para lançar a entrada.`
          );
        }
      }

      await queryClient.invalidateQueries({ queryKey: ['produtos'] });
      await queryClient.invalidateQueries({ queryKey: ['estoque'] });
      handleClose();
    } catch (error) {
      const message = getErrorMessage(error, 'Erro ao salvar produto');
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  // ── FORM CONTENT ──────────────────────────────────────────────────────────
  const formContent = (
    <div className={`produto-form-modal${isModal ? ' is-modal' : ''}`}>
      {/* Header */}
      <div className="pfm-header">
        <div className="pfm-title">
          <span className="pfm-icon">{id ? <FiEdit2 /> : <FiPackage />}</span>
          <h2>{id ? 'Editar Produto' : 'Novo Produto'}</h2>
        </div>
        <button className="pfm-close" onClick={handleClose} type="button" title="Fechar">
          <FiX />
        </button>
      </div>

      {loading ? (
        <div className="pfm-loading">Carregando...</div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="pfm-form">

          {/* Nome */}
          <div className="pfm-group">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              type="text"
              placeholder="Nome do produto"
              {...register('nome')}
              className={errors.nome ? 'invalid' : ''}
            />
            {errors.nome && <span className="pfm-error">{errors.nome.message}</span>}
          </div>

          {/* Categoria */}
          <div className="pfm-group">
            <label htmlFor="categoria_id">Categoria *</label>
            <select
              id="categoria_id"
              {...register('categoria_id')}
              className={errors.categoria_id ? 'invalid' : ''}
            >
              <option value="">Selecionar...</option>
              {categorias.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.nome}
                </option>
              ))}
            </select>
            {errors.categoria_id && (
              <span className="pfm-error">{errors.categoria_id.message}</span>
            )}
          </div>

          {/* Preço de Venda + Custo + Promocional */}
          <div className="pfm-row pfm-row-3">
            <div className="pfm-group">
              <label htmlFor="preco">Preço de Venda *</label>
              <input
                id="preco"
                type="number"
                step="0.01"
                min="0"
                placeholder="0,00"
                {...register('preco')}
                className={errors.preco ? 'invalid' : ''}
              />
              {errors.preco && <span className="pfm-error">{errors.preco.message}</span>}
            </div>
            <div className="pfm-group">
              <label htmlFor="custo">Custo</label>
              <input
                id="custo"
                type="number"
                step="0.01"
                min="0"
                placeholder="0,00"
                {...register('custo')}
                className={errors.custo ? 'invalid' : ''}
              />
              {errors.custo && <span className="pfm-error">{errors.custo.message}</span>}
            </div>
            <div className="pfm-group">
              <label htmlFor="preco_promocional">Preço Promocional</label>
              <input
                id="preco_promocional"
                type="number"
                step="0.01"
                min="0"
                placeholder="Opcional"
                {...register('preco_promocional')}
                className={errors.preco_promocional ? 'invalid' : ''}
              />
              {errors.preco_promocional && (
                <span className="pfm-error">{errors.preco_promocional.message}</span>
              )}
            </div>
          </div>

          {/* Unidade + Status */}
          <div className="pfm-row">
            <div className="pfm-group">
              <label htmlFor="unidade_medida">Unidade *</label>
              <select
                id="unidade_medida"
                {...register('unidade_medida')}
                className={errors.unidade_medida ? 'invalid' : ''}
              >
                {UNIDADES_MEDIDA.map((unidade) => (
                  <option key={unidade.codigo} value={unidade.codigo}>
                    {unidade.codigo} — {unidade.label}
                  </option>
                ))}
              </select>
              {errors.unidade_medida && (
                <span className="pfm-error">{errors.unidade_medida.message}</span>
              )}
            </div>
            <div className="pfm-group pfm-group--checkbox">
              <label htmlFor="ativo">
                <input id="ativo" type="checkbox" {...register('ativo')} /> Produto ativo
              </label>
            </div>
          </div>

          {/* Estoque inicial — apenas na criação; a gestão contínua é da tela de Estoque */}
          {!id && (
            <div className="pfm-row">
              <div className="pfm-group">
                <label htmlFor="estoque_inicial">Estoque Inicial</label>
                <input
                  id="estoque_inicial"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0"
                  disabled={!produtoAtivo}
                  {...register('estoque_inicial')}
                  className={errors.estoque_inicial ? 'invalid' : ''}
                />
                {errors.estoque_inicial && (
                  <span className="pfm-error">{errors.estoque_inicial.message}</span>
                )}
              </div>
              <div className="pfm-group">
                <label htmlFor="estoque_minimo">Est. Mínimo</label>
                <input
                  id="estoque_minimo"
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="0"
                  disabled={!produtoAtivo}
                  {...register('estoque_minimo')}
                  className={errors.estoque_minimo ? 'invalid' : ''}
                />
                {errors.estoque_minimo && (
                  <span className="pfm-error">{errors.estoque_minimo.message}</span>
                )}
              </div>
            </div>
          )}

          {/* Descrição */}
          <div className="pfm-group">
            <label htmlFor="descricao">Descrição</label>
            <textarea
              id="descricao"
              placeholder="Descrição do produto"
              rows={3}
              {...register('descricao')}
              className={errors.descricao ? 'invalid' : ''}
            />
            {errors.descricao && <span className="pfm-error">{errors.descricao.message}</span>}
          </div>

          {/* Actions */}
          <div className="pfm-actions">
            <button type="button" className="pfm-btn-cancel" onClick={handleClose}>Cancelar</button>
            <button type="submit" className="pfm-btn-save" disabled={submitting}>
              {submitting ? 'Salvando...' : 'Salvar'}
            </button>
          </div>
        </form>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="pfm-overlay">
        {formContent}
      </div>
    );
  }

  // Standalone page fallback (rota /produtos/novo e /produtos/:id/editar)
  return <div className="produto-form-page">{formContent}</div>;
};

export default ProdutoFormPage;
