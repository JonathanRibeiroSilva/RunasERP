/**
 * Leitura do XML de NF-e que o fornecedor já entrega. Sem webservice nem
 * certificado: buscar a nota pela chave exige certificado A1/A3 (card 41).
 */

/** Um jeito de contar o item: a nota traz a unidade comercial e a tributável, cada uma com seu GTIN. */
export interface CandidatoItem {
  codigo: string;
  quantidade: number;
  custoUnitario: number;
}

export interface ItemNfe {
  descricao: string;
  /** Na ordem de preferência: comercial (cEAN/qCom) e depois tributável (cEANTrib/qTrib). */
  candidatos: CandidatoItem[];
}

export interface Nfe {
  numero: string;
  chave: string;
  emitente: string;
  itens: ItemNfe[];
}

const primeiro = (el: Element | Document | undefined, tag: string) =>
  el?.getElementsByTagNameNS('*', tag)[0];

const texto = (el: Element | Document | undefined, tag: string) =>
  primeiro(el, tag)?.textContent?.trim() ?? '';

/** GTIN tem 8 a 14 dígitos; produto sem código vem como "SEM GTIN". */
const ehGtin = (valor: string) => /^\d{8,14}$/.test(valor);

const candidato = (det: Element, gtin: string, qtd: string, custo: string): CandidatoItem[] => {
  const codigo = texto(det, gtin);
  return ehGtin(codigo)
    ? [{ codigo, quantidade: Number(texto(det, qtd)), custoUnitario: Number(texto(det, custo)) }]
    : [];
};

export const lerNfe = (xml: string): Nfe => {
  const doc = new DOMParser().parseFromString(xml, 'application/xml');
  const inf = primeiro(doc, 'infNFe');
  if (doc.getElementsByTagName('parsererror').length > 0 || !inf) {
    throw new Error('O arquivo não é o XML de uma NF-e.');
  }

  const itens = Array.from(inf.getElementsByTagNameNS('*', 'det')).map((det) => {
    const comercial = candidato(det, 'cEAN', 'qCom', 'vUnCom');
    const tributavel = candidato(det, 'cEANTrib', 'qTrib', 'vUnTrib');
    return {
      descricao: texto(det, 'xProd'),
      candidatos: [...comercial, ...tributavel.filter((t) => t.codigo !== comercial[0]?.codigo)],
    };
  });

  const numero = texto(primeiro(inf, 'ide'), 'nNF');
  const chave = (inf.getAttribute('Id') ?? '').replace(/^NFe/, '');
  // A chave é o que o estoque usa para não dar entrada na mesma nota duas vezes.
  if (!/^\d{44}$/.test(chave) || !/^\d{1,9}$/.test(numero)) {
    throw new Error('O arquivo não é o XML de uma NF-e.');
  }

  return { numero, chave, emitente: texto(primeiro(inf, 'emit'), 'xNome'), itens };
};
