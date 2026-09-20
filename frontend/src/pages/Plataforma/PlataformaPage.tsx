import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FiGrid, FiPlus, FiPause, FiPlay, FiTag, FiActivity, FiUsers, FiDollarSign, FiAlertTriangle, FiSlash } from 'react-icons/fi';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCNPJ } from '@/utils/validators';
import { getErrorMessage } from '@/services/api/axios';
import {
  useTenants,
  useCriarTenant,
  useDefinirAcessoTenant,
  useAlterarPlano,
} from '@/hooks/usePlataforma';
import type { Tenant } from '@/types/plataforma';
import {
  tenantSchema,
  planoSchema,
  type TenantFormData,
  type PlanoFormData,
} from './tenantSchema';
import { valorParaNumero } from './assinaturaSchema';
import TenantDetalhe from './TenantDetalhe';

const REGIMES: Array<{ value: TenantFormData['regime_tributario']; label: string }> = [
  { value: 'SIMPLES_NACIONAL', label: 'Simples Nacional' },
  { value: 'LUCRO_PRESUMIDO', label: 'Lucro Presumido' },
  { value: 'LUCRO_REAL', label: 'Lucro Real' },
  { value: 'MEI', label: 'MEI' },
];

/** Campos de texto simples do provisionamento; CNPJ, CEP e regime têm tratamento próprio. */
const CAMPOS: Array<{ name: keyof TenantFormData; label: string }> = [
  { name: 'razao_social', label: 'Razão social *' },
  { name: 'nome_fantasia', label: 'Nome fantasia *' },
  { name: 'slug', label: 'Slug da loja *' },
  { name: 'logradouro', label: 'Logradouro *' },
  { name: 'numero', label: 'Número *' },
  { name: 'complemento', label: 'Complemento' },
  { name: 'bairro', label: 'Bairro *' },
  { name: 'cidade', label: 'Cidade *' },
  { name: 'uf', label: 'UF *' },
  { name: 'telefone', label: 'Telefone' },
  { name: 'email', label: 'E-mail da empresa' },
  { name: 'admin_nome', label: 'Nome do administrador *' },
  { name: 'admin_email', label: 'E-mail do administrador *' },
];

const VAZIO: TenantFormData = {
  razao_social: '', nome_fantasia: '', slug: '', cnpj: '',
  inscricao_estadual: '', inscricao_municipal: '', regime_tributario: 'SIMPLES_NACIONAL',
  cep: '', logradouro: '', numero: '', complemento: '', bairro: '', cidade: '', uf: '',
  telefone: '', celular: '', email: '', site: '',
  plano: 'BASICO', max_usuarios: '5',
  admin_nome: '', admin_email: '', admin_senha: '',
};

/**
 * Os números do negócio, derivados da lista que a página já carregou.
 *
 * Sem endpoint novo: GET /plataforma/tenants já devolve status, assinatura e
 * usuários ativos de cada lojista. Uma rota de agregação no gateway só faria no
 * Postgres o que aqui é um reduce sobre dados que já estão na memória.
 */
export const resumirTenants = (tenants: Tenant[]) => ({
  lojistas: tenants.length,
  ativos: tenants.filter((t) => t.ativo).length,
  // Só ATIVA entra no MRR: PENDENTE ainda não foi paga e INADIMPLENTE parou de
  // ser paga — somar as duas infla a receita com dinheiro que não entrou.
  mrr: tenants.reduce(
    (soma, t) => soma + (t.assinatura?.status === 'ATIVA' ? valorParaNumero(t.assinatura.valor) : 0),
    0,
  ),
  // INADIMPLENTE (escrita bloqueada) e SUSPENSA (acesso cortado) são o mesmo
  // trabalho para você: cobrar. Contar junto evita dois cartões dizendo o mesmo.
  aCobrar: tenants.filter(
    (t) => t.assinatura?.status === 'INADIMPLENTE' || t.assinatura?.status === 'SUSPENSA',
  ).length,
  // Provisionado e nunca cobrado: cortesia, teste — ou uma cobrança esquecida.
  semAssinatura: tenants.filter((t) => t.assinatura === null).length,
});

const PlataformaPage = () => {
  const { data, isLoading } = useTenants();
  const criar = useCriarTenant();
  const definirAcesso = useDefinirAcessoTenant();
  const alterarPlano = useAlterarPlano();

  const [novoAberto, setNovoAberto] = useState(false);
  const [tenantPlano, setTenantPlano] = useState<Tenant | null>(null);
  const [tenantDetalhe, setTenantDetalhe] = useState<Tenant | null>(null);
  // Erro do backend ao lado do form que o causou (slug/CNPJ duplicado, e-mail já usado).
  const [erro, setErro] = useState<string | null>(null);

  const tenantForm = useForm<TenantFormData>({
    resolver: zodResolver(tenantSchema),
    defaultValues: VAZIO,
  });
  const planoForm = useForm<PlanoFormData>({ resolver: zodResolver(planoSchema) });

  const tenants = data?.items ?? [];
  const resumo = resumirTenants(tenants);

  const abrirNovo = () => {
    setErro(null);
    tenantForm.reset(VAZIO);
    setNovoAberto(true);
  };

  const abrirPlano = (tenant: Tenant) => {
    setErro(null);
    planoForm.reset({
      plano: tenant.plano,
      max_usuarios: String(tenant.max_usuarios),
      max_produtos: String(tenant.max_produtos),
    });
    setTenantPlano(tenant);
  };

  const submitTenant = async (form: TenantFormData) => {
    setErro(null);
    const { admin_nome, admin_email, admin_senha, max_usuarios, ...empresa } = form;
    try {
      await criar.mutateAsync({
        empresa: { ...empresa, max_usuarios: Number(max_usuarios) },
        admin: { nome: admin_nome, email: admin_email, senha: admin_senha },
      });
      toast.success('Tenant provisionado');
      setNovoAberto(false);
    } catch (error) {
      setErro(getErrorMessage(error, 'Erro ao provisionar tenant'));
    }
  };

  const submitPlano = async (form: PlanoFormData) => {
    if (!tenantPlano) return;
    setErro(null);
    try {
      await alterarPlano.mutateAsync({
        id: tenantPlano.id,
        data: {
          plano: form.plano,
          max_usuarios: Number(form.max_usuarios),
          max_produtos: form.max_produtos === '' ? null : Number(form.max_produtos),
        },
      });
      toast.success('Plano atualizado');
      setTenantPlano(null);
    } catch (error) {
      setErro(getErrorMessage(error, 'Erro ao alterar plano'));
    }
  };

  const handleAcesso = (tenant: Tenant) => {
    const acao = tenant.ativo ? 'suspender' : 'reativar';
    if (!window.confirm(`Confirma ${acao} o tenant ${tenant.nome_fantasia}?`)) return;
    definirAcesso.mutate(
      { id: tenant.id, acao },
      {
        onSuccess: () => toast.success(`Tenant ${acao === 'suspender' ? 'suspenso' : 'reativado'}`),
        onError: (error) => toast.error(getErrorMessage(error, 'Erro ao alterar acesso')),
      }
    );
  };

  return (
    <div className="admin-list">
      <div className="page-header">
        <h1><FiGrid className="title-icon" /> Plataforma</h1>
        <p className="page-description">
          Provisione e administre os tenants. Nenhuma rota daqui lê dado de negócio dos lojistas.
        </p>
      </div>

      <div className="stats-grid">
        <div className="stat-card stat-primary">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiUsers /></div></div>
          <div className="stat-content">
            <p className="stat-title">Lojistas</p>
            <h3 className="stat-value font-mono">{resumo.lojistas}</h3>
            <span className="stat-change">{resumo.ativos} com acesso liberado</span>
          </div>
        </div>
        <div className="stat-card stat-success">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiDollarSign /></div></div>
          <div className="stat-content">
            <p className="stat-title">Receita mensal</p>
            <h3 className="stat-value font-mono">
              {resumo.mrr.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </h3>
            <span className="stat-change">apenas assinaturas ativas</span>
          </div>
        </div>
        <div className="stat-card stat-warning">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiAlertTriangle /></div></div>
          <div className="stat-content">
            <p className="stat-title">A cobrar</p>
            <h3 className="stat-value font-mono">{resumo.aCobrar}</h3>
            <span className="stat-change">inadimplentes ou suspensos</span>
          </div>
        </div>
        <div className="stat-card stat-secondary">
          <div className="stat-icon-wrapper"><div className="stat-icon"><FiSlash /></div></div>
          <div className="stat-content">
            <p className="stat-title">Sem assinatura</p>
            <h3 className="stat-value font-mono">{resumo.semAssinatura}</h3>
            <span className="stat-change">provisionados e nunca cobrados</span>
          </div>
        </div>
      </div>

      <div className="list-header">
        <span className="list-counter">{data?.total ?? 0} tenants</span>
        <button className="btn btn-primary" onClick={abrirNovo}>
          <FiPlus /> Novo Tenant
        </button>
      </div>

      {isLoading ? (
        <div className="empty-state">Carregando...</div>
      ) : tenants.length === 0 ? (
        <div className="empty-state">Nenhum tenant cadastrado</div>
      ) : (
        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Empresa</th>
                <th>CNPJ</th>
                <th>Cidade</th>
                <th>Plano</th>
                <th>Usuários</th>
                <th>Cobrança</th>
                <th>Status</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((t) => (
                <tr key={t.id} className={t.ativo ? '' : 'inactive'}>
                  <td data-label="Empresa">
                    {t.nome_fantasia}
                    <small className="sub">/c/{t.slug}</small>
                  </td>
                  <td data-label="CNPJ">{t.cnpj}</td>
                  <td data-label="Cidade">{t.cidade}/{t.uf}</td>
                  <td data-label="Plano"><span className="badge badge-info">{t.plano}</span></td>
                  <td data-label="Usuários">{t.usuarios_ativos}</td>
                  <td data-label="Cobrança">
                    {t.assinatura === null ? (
                      <span className="badge">Sem assinatura</span>
                    ) : (
                      <span
                        className={
                          t.assinatura.somente_leitura
                            ? 'badge badge-danger'
                            : 'badge badge-success'
                        }
                        // Somente leitura é o estágio antes da suspensão: o
                        // lojista ainda entra e lê, mas toda escrita volta 402.
                        title={
                          t.assinatura.somente_leitura
                            ? 'Escrita bloqueada por fatura em aberto'
                            : `Vence em ${t.assinatura.vence_em ?? '—'}`
                        }
                      >
                        {t.assinatura.somente_leitura ? 'Somente leitura' : t.assinatura.status}
                      </span>
                    )}
                  </td>
                  <td data-label="Status">
                    <span className={`badge ${t.ativo ? 'badge-success' : 'badge-error'}`}>
                      {t.status}
                    </span>
                  </td>
                  <td data-label="Ações">
                    <div className="actions-group">
                      <button className="btn btn-sm btn-outline-primary" onClick={() => abrirPlano(t)} title="Plano">
                        <FiTag />
                      </button>
                      <button
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => setTenantDetalhe(t)}
                        title="Auditoria, assinatura e backups"
                      >
                        <FiActivity />
                      </button>
                      <button
                        className={`btn btn-sm ${t.ativo ? 'btn-outline-danger' : 'btn-outline-success'}`}
                        onClick={() => handleAcesso(t)}
                        title={t.ativo ? 'Suspender' : 'Reativar'}
                      >
                        {t.ativo ? <FiPause /> : <FiPlay />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={novoAberto} title="Provisionar tenant" onClose={() => setNovoAberto(false)}>
        <form className="admin-form" onSubmit={tenantForm.handleSubmit(submitTenant)}>
          {erro && <div className="form-error">{erro}</div>}

          <div className="form-row">
            <div className="form-group">
              <Controller
                name="cnpj"
                control={tenantForm.control}
                render={({ field }) => (
                  <MaskedInput
                    mask="cnpj"
                    label="CNPJ"
                    required
                    placeholder="00.000.000/0000-00"
                    value={field.value ?? ''}
                    onChange={field.onChange}
                    onValidate={validateCNPJ}
                    error={tenantForm.formState.errors.cnpj?.message}
                  />
                )}
              />
            </div>
            <div className="form-group">
              <Controller
                name="cep"
                control={tenantForm.control}
                render={({ field }) => (
                  <MaskedInput
                    mask="cep"
                    label="CEP"
                    required
                    placeholder="00000-000"
                    value={field.value ?? ''}
                    onChange={field.onChange}
                    error={tenantForm.formState.errors.cep?.message}
                  />
                )}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="regime_tributario">Regime tributário *</label>
            <select id="regime_tributario" {...tenantForm.register('regime_tributario')}>
              {REGIMES.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          {CAMPOS.map((c) => (
            <div className="form-group" key={c.name}>
              <label htmlFor={c.name}>{c.label}</label>
              <input id={c.name} type="text" {...tenantForm.register(c.name)} />
              {tenantForm.formState.errors[c.name] && (
                <span className="field-error">{tenantForm.formState.errors[c.name]?.message}</span>
              )}
            </div>
          ))}

          <div className="form-group">
            <label htmlFor="admin_senha">Senha do administrador *</label>
            <input
              id="admin_senha"
              type="password"
              autoComplete="new-password"
              {...tenantForm.register('admin_senha')}
            />
            {tenantForm.formState.errors.admin_senha && (
              <span className="field-error">{tenantForm.formState.errors.admin_senha.message}</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="plano">Plano *</label>
              <input id="plano" type="text" {...tenantForm.register('plano')} />
              {tenantForm.formState.errors.plano && (
                <span className="field-error">{tenantForm.formState.errors.plano.message}</span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="max_usuarios">Máximo de usuários *</label>
              <input id="max_usuarios" type="text" {...tenantForm.register('max_usuarios')} />
              {tenantForm.formState.errors.max_usuarios && (
                <span className="field-error">{tenantForm.formState.errors.max_usuarios.message}</span>
              )}
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setNovoAberto(false)}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={tenantForm.formState.isSubmitting}>
              Provisionar
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={tenantPlano !== null}
        title={`Plano — ${tenantPlano?.nome_fantasia ?? ''}`}
        onClose={() => setTenantPlano(null)}
      >
        <form className="admin-form" onSubmit={planoForm.handleSubmit(submitPlano)}>
          {erro && <div className="form-error">{erro}</div>}

          <div className="form-group">
            <label htmlFor="plano_nome">Plano *</label>
            <input id="plano_nome" type="text" {...planoForm.register('plano')} />
            {planoForm.formState.errors.plano && (
              <span className="field-error">{planoForm.formState.errors.plano.message}</span>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="plano_max_usuarios">Máximo de usuários *</label>
              <input id="plano_max_usuarios" type="text" {...planoForm.register('max_usuarios')} />
              {planoForm.formState.errors.max_usuarios && (
                <span className="field-error">{planoForm.formState.errors.max_usuarios.message}</span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="plano_max_produtos">Máximo de produtos</label>
              <input
                id="plano_max_produtos"
                type="text"
                placeholder="vazio = sem limite"
                {...planoForm.register('max_produtos')}
              />
              {planoForm.formState.errors.max_produtos && (
                <span className="field-error">{planoForm.formState.errors.max_produtos.message}</span>
              )}
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={() => setTenantPlano(null)}>
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={planoForm.formState.isSubmitting}>
              Salvar
            </button>
          </div>
        </form>
      </Modal>
      <TenantDetalhe tenant={tenantDetalhe} onClose={() => setTenantDetalhe(null)} />
    </div>
  );
};

export default PlataformaPage;
