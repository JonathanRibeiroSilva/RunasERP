import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';
import { FiExternalLink, FiSave, FiSettings } from 'react-icons/fi';
import { useAuth } from '@/hooks/useAuth';
import { useEmpresa, useAtualizarEmpresa, useProdutosLoja, usePublicarProduto } from '@/hooks/useLojaOnline';
import { getErrorMessage } from '@/services/api/axios';
import type { EmpresaStoreConfigUpdate } from '@/types/empresa';
import './LojaOnline.scss';

/** Gera o slug URL-safe a partir de um nome (mesma regra validada no backend). */
const gerarSlug = (nome: string): string =>
  nome
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

const ConfiguracoesLojaPage = () => {
  const { user } = useAuth();
  const { data: empresa, isLoading: carregandoEmpresa } = useEmpresa(user?.empresa_id);
  const atualizarEmpresa = useAtualizarEmpresa(user?.empresa_id);
  const { data: produtosLoja, isLoading: carregandoProdutos } = useProdutosLoja({ limit: 100 });
  const publicarProduto = usePublicarProduto();

  const [form, setForm] = useState<EmpresaStoreConfigUpdate>({});

  useEffect(() => {
    if (!empresa) return;
    setForm({
      catalogo_ativo: empresa.catalogo_ativo,
      catalogo_titulo: empresa.catalogo_titulo ?? '',
      catalogo_descricao: empresa.catalogo_descricao ?? '',
      catalogo_whatsapp: empresa.catalogo_whatsapp ?? '',
      logo_url: empresa.logo_url ?? '',
      cor_primaria: empresa.cor_primaria ?? '#3B82F6',
      cor_secundaria: empresa.cor_secundaria ?? '#10B981',
    });
  }, [empresa]);

  // Título alterado ⇒ o backend regenera o slug automaticamente ao salvar.
  const tituloAlterado =
    !!empresa && (form.catalogo_titulo ?? '') !== (empresa.catalogo_titulo ?? '');
  const slugPrevisto = gerarSlug(form.catalogo_titulo || '');
  const enderecoVaiMudar = tituloAlterado && !!slugPrevisto && slugPrevisto !== empresa?.slug;

  const handleToggleAtiva = async (ativo: boolean) => {
    setForm((prev) => ({ ...prev, catalogo_ativo: ativo }));
    try {
      await atualizarEmpresa.mutateAsync({ catalogo_ativo: ativo });
      toast.success(ativo ? 'Loja ativada' : 'Loja desativada');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao atualizar loja'));
    }
  };

  const handleSalvarConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await atualizarEmpresa.mutateAsync(form);
      toast.success(
        enderecoVaiMudar
          ? 'Configurações salvas — o endereço da loja mudou junto com o nome; links antigos deixaram de funcionar'
          : 'Configurações da loja salvas com sucesso'
      );
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao salvar configurações'));
    }
  };

  const handleTogglePublicado = async (produtoId: string, visivel: boolean) => {
    try {
      await publicarProduto.mutateAsync({ produtoId, data: { visivel } });
      toast.success(visivel ? 'Produto publicado na loja' : 'Produto removido da loja');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao atualizar publicação do produto'));
    }
  };

  if (carregandoEmpresa) {
    return (
      <div className="page-container">
        <div className="loading">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="page-container configuracoes-loja-page">
      <div className="page-header">
        <h1><FiSettings className="title-icon" /> Configurações da Loja</h1>
        <p className="page-description">
          Ative sua loja, personalize a apresentação e publique produtos do catálogo.
        </p>
      </div>

      <div className="form-section loja-status">
        <div className="loja-status-info">
          <h2>Status da loja</h2>
          <p>
            {empresa?.catalogo_ativo
              ? 'Sua loja está ativa e visível publicamente.'
              : 'Sua loja está desativada — clientes não conseguem acessá-la.'}
          </p>
          {empresa?.slug && (
            <a
              href={`/c/${empresa.slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="loja-preview-link"
            >
              <FiExternalLink /> Ver loja pública
            </a>
          )}
        </div>
        <label className="switch">
          <input
            type="checkbox"
            checked={!!form.catalogo_ativo}
            onChange={(e) => handleToggleAtiva(e.target.checked)}
          />
          <span className="slider" />
        </label>
      </div>

      <div className="form-section">
        <h2>Aparência e contato</h2>
        <form onSubmit={handleSalvarConfig}>
          <div className="form-group">
            <label htmlFor="catalogo_titulo">Título da loja</label>
            <input
              id="catalogo_titulo"
              type="text"
              value={form.catalogo_titulo || ''}
              onChange={(e) => setForm({ ...form, catalogo_titulo: e.target.value })}
              placeholder="Nome exibido na loja"
            />
          </div>

          <div className="form-group">
            <label>Endereço da loja (link público)</label>
            <div className="slug-input-row">
              <span className="slug-prefixo">
                /c/{enderecoVaiMudar ? slugPrevisto : empresa?.slug}
              </span>
            </div>
            {enderecoVaiMudar && (
              <p className="slug-aviso">
                Atenção: ao salvar, o endereço muda de /c/{empresa?.slug} para /c/{slugPrevisto}
                {' '}— links, QR codes e mensagens já enviadas com o link antigo deixarão de
                funcionar.
              </p>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="catalogo_descricao">Descrição</label>
            <textarea
              id="catalogo_descricao"
              rows={3}
              value={form.catalogo_descricao || ''}
              onChange={(e) => setForm({ ...form, catalogo_descricao: e.target.value })}
              placeholder="Texto de apresentação da loja"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="catalogo_whatsapp">WhatsApp de contato</label>
              <input
                id="catalogo_whatsapp"
                type="text"
                value={form.catalogo_whatsapp || ''}
                onChange={(e) => setForm({ ...form, catalogo_whatsapp: e.target.value })}
                placeholder="(00) 00000-0000"
              />
            </div>

            <div className="form-group">
              <label htmlFor="logo_url">URL do logotipo</label>
              <input
                id="logo_url"
                type="text"
                value={form.logo_url || ''}
                onChange={(e) => setForm({ ...form, logo_url: e.target.value })}
                placeholder="https://..."
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cor_primaria">Cor primária</label>
              <input
                id="cor_primaria"
                type="color"
                value={form.cor_primaria || '#3B82F6'}
                onChange={(e) => setForm({ ...form, cor_primaria: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="cor_secundaria">Cor secundária</label>
              <input
                id="cor_secundaria"
                type="color"
                value={form.cor_secundaria || '#10B981'}
                onChange={(e) => setForm({ ...form, cor_secundaria: e.target.value })}
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={atualizarEmpresa.isPending}>
              <FiSave /> {atualizarEmpresa.isPending ? 'Salvando...' : 'Salvar configurações'}
            </button>
          </div>
        </form>
      </div>

      <div className="form-section">
        <h2>Produtos na loja</h2>
        <p className="section-hint">
          Só produtos publicados aqui aparecem na loja pública. Ative os que quiser vender online.
        </p>

        {carregandoProdutos ? (
          <div className="loading">Carregando produtos...</div>
        ) : !produtosLoja?.items.length ? (
          <div className="empty-state-small">
            <p>Nenhum produto ativo cadastrado ainda.</p>
          </div>
        ) : (
          <div className="produtos-loja-table">
            {produtosLoja.items.map((produto) => (
              <div key={produto.id} className="produto-loja-row">
                <div className="produto-loja-info">
                  <span className="nome">{produto.nome}</span>
                  <span className={`badge ${produto.visivel ? 'badge-success' : 'badge-secondary'}`}>
                    {produto.visivel ? 'Publicado' : 'Não publicado'}
                  </span>
                </div>
                <label className="switch switch-small">
                  <input
                    type="checkbox"
                    checked={produto.visivel}
                    onChange={(e) => handleTogglePublicado(produto.id, e.target.checked)}
                  />
                  <span className="slider" />
                </label>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ConfiguracoesLojaPage;
