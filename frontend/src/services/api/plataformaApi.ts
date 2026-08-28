import type { AxiosRequestConfig } from 'axios';
import { api } from './axios';
import { env } from '@/config/env';
import type {
  TenantsListResult,
  TenantCreatePayload,
  PlanoPayload,
  AuditoriaResult,
  DumpsResult,
  AssinaturaPayload,
  AssinaturaLink,
} from '@/types/plataforma';

/** Camada de serviço da plataforma — todas as rotas exigem SUPER_ADMIN no gateway. */
export const plataformaApi = {
  listarTenants(config?: AxiosRequestConfig) {
    return api.get<TenantsListResult>('/plataforma/tenants', config).then((r) => r.data);
  },

  criarTenant(data: TenantCreatePayload) {
    return api.post('/plataforma/tenants', data).then((r) => r.data);
  },

  /** Suspender/reativar mexe no status da empresa E no ativo dos usuários dela. */
  definirAcesso(id: number, acao: 'suspender' | 'reativar') {
    return api.patch(`/plataforma/tenants/${id}/${acao}`).then((r) => r.data);
  },

  alterarPlano(id: number, data: PlanoPayload) {
    return api.patch(`/plataforma/tenants/${id}/plano`, data).then((r) => r.data);
  },

  auditoria(id: number, config?: AxiosRequestConfig) {
    return api
      .get<AuditoriaResult>(`/plataforma/tenants/${id}/auditoria`, { params: { limit: 50 }, ...config })
      .then((r) => r.data);
  },

  reverter(registroId: number) {
    return api.post(`/plataforma/auditoria/${registroId}/reverter`).then((r) => r.data);
  },

  dumps(id: number, config?: AxiosRequestConfig) {
    return api.get<DumpsResult>(`/plataforma/tenants/${id}/dumps`, config).then((r) => r.data);
  },

  criarAssinatura(id: number, data: AssinaturaPayload) {
    return api.post<AssinaturaLink>(`/plataforma/tenants/${id}/assinatura`, data).then((r) => r.data);
  },

  cancelarAssinatura(id: number) {
    return api.delete(`/plataforma/tenants/${id}/assinatura`).then((r) => r.data);
  },

  /**
   * Exportação é StreamingResponse com Content-Disposition: attachment.
   * O navegador baixa direto pelo cookie de sessão; puxar por axios carregaria
   * o tenant inteiro em memória só para reemitir o mesmo download.
   */
  urlExportar(id: number) {
    return `${env.apiUrl}/plataforma/tenants/${id}/exportar`;
  },
};
