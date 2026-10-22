import { describe, expect, it } from 'vitest';
import { lerNfe } from '../nfeXml';

const det = (n: number, cEAN: string, cEANTrib: string, qCom: string, qTrib: string) => `
  <det nItem="${n}"><prod>
    <cEAN>${cEAN}</cEAN><xProd>Item ${n}</xProd><qCom>${qCom}</qCom><vUnCom>60.00</vUnCom>
    <cEANTrib>${cEANTrib}</cEANTrib><qTrib>${qTrib}</qTrib><vUnTrib>5.00</vUnTrib>
  </prod></det>`;

const XML = `<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe Id="NFe35261012345678000199550010000012341000012345">
  <ide><nNF>1234</nNF></ide>
  <emit><xNome>Distribuidora Exemplo</xNome></emit>
  <dest><xNome>Loja Cliente</xNome></dest>
  ${det(1, '17891000100103', '7891000100103', '2', '24')}
  ${det(2, 'SEM GTIN', 'SEM GTIN', '1', '1')}
  ${det(3, '7894900011012', '7894900011012', '6', '6')}
</infNFe></NFe></nfeProc>`;

describe('lerNfe', () => {
  const nfe = lerNfe(XML);

  it('lê cabeçalho sem confundir emitente com destinatário', () => {
    expect(nfe.numero).toBe('1234');
    expect(nfe.chave).toBe('35261012345678000199550010000012341000012345');
    expect(nfe.emitente).toBe('Distribuidora Exemplo');
  });

  it('caixa e unidade viram dois candidatos, cada um com sua quantidade e custo', () => {
    expect(nfe.itens[0].candidatos).toEqual([
      { codigo: '17891000100103', quantidade: 2, custoUnitario: 60 },
      { codigo: '7891000100103', quantidade: 24, custoUnitario: 5 },
    ]);
  });

  it('SEM GTIN não vira candidato e GTIN repetido não duplica', () => {
    expect(nfe.itens[1].candidatos).toEqual([]);
    expect(nfe.itens[2].candidatos).toHaveLength(1);
  });

  it('recusa arquivo que não é NF-e', () => {
    expect(() => lerNfe('<pedido/>')).toThrow();
    expect(() => lerNfe('não é xml')).toThrow();
  });

  it('recusa nota sem a chave de 44 dígitos, que é o que impede a entrada em dobro', () => {
    expect(() => lerNfe(XML.replace(/Id="NFe\d+"/, 'Id="NFe123"'))).toThrow();
    expect(() => lerNfe(XML.replace(/ Id="NFe\d+"/, ''))).toThrow();
  });
});
