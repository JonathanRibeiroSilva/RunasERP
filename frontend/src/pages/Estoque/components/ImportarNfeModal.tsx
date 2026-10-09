import { useState } from 'react';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import { getErrorMessage } from '@/services/api/axios';
import { produtosApi } from '@/services/api/produtosApi';
import { useEntradaEstoque } from '@/hooks/useEstoque';
import { useAuth } from '@/hooks/useAuth';
import { lerNfe, type CandidatoItem, type Nfe } from '../nfeXml';
import { formatarQuantidade } from '../estoqueFormat';

interface Props {
  onClose: () => void;
}

interface Linha {
  descricao: string;
  produto: { id: string; nome: string } | null;
  uso?: CandidatoItem;
}

const moeda = (valor: number) => valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

/** Casa código → produto como o campo de leitura da página: só EAN exato e sem ambiguidade. */
const casarPorCodigo = async (codigos: string[]) => {
  const pares = await Promise.all(
    codigos.map(async (codigo) => {
      const { items } = await produtosApi.listar({ busca: codigo, limit: 10 });
      const achados = items.filter((p) => p.codigo_barras === codigo);
      return [codigo, achados.length === 1 ? achados[0] : null] as const;
    }),
  );
  return new Map(pares);
};

const ImportarNfeModal: React.FC<Props> = ({ onClose }) => {
  const { user } = useAuth();
  const entrada = useEntradaEstoque();
  const [nfe, setNfe] = useState<Nfe | null>(null);
  const [linhas, setLinhas] = useState<Linha[]>([]);
  const [lendo, setLendo] = useState(false);
  const [gravando, setGravando] = useState(false);

  const abrirArquivo = async (arquivo?: File) => {
    if (!arquivo) return;
    setLendo(true);
    try {
      const lida = lerNfe(await arquivo.text());
      const codigos = [...new Set(lida.itens.flatMap((item) => item.candidatos.map((c) => c.codigo)))];
      const produtos = await casarPorCodigo(codigos);
      setLinhas(
        lida.itens.map((item) => {
          // Caixa ou unidade: vale o GTIN que estiver cadastrado, com a quantidade dele.
          const uso = item.candidatos.find((c) => produtos.get(c.codigo));
          return { descricao: item.descricao, uso, produto: uso ? produtos.get(uso.codigo)! : null };
        }),
      );
      setNfe(lida);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Não foi possível ler a nota'));
    } finally {
      setLendo(false);
    }
  };

  const casadas = linhas.filter((linha) => linha.produto && linha.uso);

  const darEntrada = async () => {
    if (!nfe) return;
    setGravando(true);
    const falhas: string[] = [];
    // ponytail: uma chamada por item e sem trava de nota repetida; entrada em lote
    // idempotente pela chave da NF-e exige endpoint novo no serviço de estoque.
    for (const linha of casadas) {
      try {
        await entrada.mutateAsync({
          empresa_id: user!.empresa_id,
          produto_id: linha.produto!.id,
          quantidade: linha.uso!.quantidade,
          custo_unitario: linha.uso!.custoUnitario,
          motivo: 'Entrada por XML de NF-e',
          documento: `NF-e ${nfe.numero}`,
          observacao: `${nfe.emitente} · chave ${nfe.chave}`,
        });
      } catch {
        falhas.push(linha.descricao);
      }
    }
    setGravando(false);
    const certas = casadas.length - falhas.length;
    if (certas > 0) toast.success(`Entrada registrada em ${certas} item(ns) da NF-e ${nfe.numero}`);
    // Fecha mesmo com falha: reenviar a nota repetiria as entradas que deram certo.
    if (falhas.length > 0) toast.error(`Sem entrada (lance à mão): ${falhas.join(', ')}`);
    onClose();
  };

  const footer = (
    <>
      <button type="button" className="btn btn-ghost" onClick={onClose} disabled={gravando}>
        Cancelar
      </button>
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => void darEntrada()}
        disabled={!nfe || casadas.length === 0 || gravando}
      >
        {gravando ? 'Registrando...' : `Dar entrada em ${casadas.length} item(ns)`}
      </button>
    </>
  );

  return (
    <Modal isOpen title="Importar NF-e (XML)" onClose={onClose} footer={footer}>
      {!nfe ? (
        <div className="estoque-op-form">
          <div className="form-group">
            <label htmlFor="nfe-xml">XML da nota enviado pelo fornecedor</label>
            <input
              id="nfe-xml"
              type="file"
              accept=".xml,text/xml,application/xml"
              disabled={lendo}
              onChange={(event) => void abrirArquivo(event.target.files?.[0])}
            />
          </div>
          {lendo && <p>Lendo a nota...</p>}
        </div>
      ) : (
        <>
          <p className="estoque-op-produto">
            NF-e {nfe.numero} · {nfe.emitente}
          </p>
          <div className="table-responsive">
            <table className="estoque-table">
              <thead>
                <tr>
                  <th>Item da nota</th>
                  <th className="num">Qtd.</th>
                  <th className="num">Custo un.</th>
                  <th>Produto</th>
                </tr>
              </thead>
              <tbody>
                {linhas.map((linha, i) => (
                  <tr key={i}>
                    <td>{linha.descricao}</td>
                    <td className="num">{linha.uso ? formatarQuantidade(linha.uso.quantidade) : '—'}</td>
                    <td className="num">{linha.uso ? moeda(linha.uso.custoUnitario) : '—'}</td>
                    <td>
                      {linha.produto ? (
                        linha.produto.nome
                      ) : (
                        <span className="estoque-badge estoque-badge--neutral">Sem cadastro</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {casadas.length < linhas.length && (
            <p>Itens sem cadastro ficam de fora: cadastre o código de barras no produto e lance a entrada à mão.</p>
          )}
          <p role="note">Importar a mesma nota duas vezes duplica a entrada.</p>
        </>
      )}
    </Modal>
  );
};

export default ImportarNfeModal;
