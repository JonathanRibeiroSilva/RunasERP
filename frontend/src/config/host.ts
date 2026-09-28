import type { UserRole } from '@/types/auth';

/**
 * Qual das duas aplicações este bundle deve montar, decidido pelo hostname.
 *
 * O painel da plataforma e o ERP dos lojistas são produtos diferentes para
 * públicos diferentes, e agora moram em subdomínios diferentes. Quem separa é o
 * host, não o build: uma segunda imagem só para o painel custaria outro
 * container e outro deploy numa VPS de 1 vCPU, para servir as mesmas telas.
 *
 * O ganho que importa vem do navegador, não do bundle: o cookie de sessão é
 * host-only (set_auth_cookies não manda `domain=`), então a sessão do painel não
 * existe no host do lojista — e o subdomínio pode ser fechado por IP ou
 * Cloudflare Access sem afetar nenhum cliente.
 */
const LABEL_PLATAFORMA = import.meta.env.VITE_HOST_PLATAFORMA || 'admin';

export const ehPainelPlataforma =
  window.location.hostname.split('.')[0] === LABEL_PLATAFORMA;

/**
 * Em dev o SPA roda num host só (`localhost`), e as duas aplicações convivem:
 * aplicar a separação ali trancaria o super admin fora do próprio painel na
 * máquina dele. `admin.localhost:3000` exercita o caminho de produção.
 */
export const separarPorHost = ehPainelPlataforma || !import.meta.env.DEV;

export type Porta = 'ok' | 'para-plataforma' | 'para-dashboard' | 'porta-errada';

/**
 * Para onde mandar um usuário já autenticado, dado o host em que ele entrou.
 *
 * Existe como função pura porque as duas pontas se olham: mandar o super admin
 * para /plataforma num host que não tem /plataforma, ou o lojista para
 * /dashboard num host que não tem /dashboard, fecha um laço de redirect que o
 * navegador só mostra como tela branca. 'porta-errada' é o que corta o laço.
 */
export const escolherPorta = (
  role: UserRole | undefined,
  noPainel: boolean,
  pathname: string,
  separar = true,
): Porta => {
  const ehSuper = role === 'SUPER_ADMIN';

  if (separar && noPainel && !ehSuper) return 'porta-errada';
  if (separar && !noPainel && ehSuper) return 'porta-errada';

  // /perfil vale nos dois lados: é onde cada um troca a própria senha.
  if (ehSuper) {
    return pathname.startsWith('/plataforma') || pathname.startsWith('/perfil')
      ? 'ok'
      : 'para-plataforma';
  }
  return pathname.startsWith('/plataforma') ? 'para-dashboard' : 'ok';
};
