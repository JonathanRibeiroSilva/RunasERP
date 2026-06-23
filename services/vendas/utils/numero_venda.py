"""
Utilitário para geração de número de venda.
"""
from datetime import datetime


def gerar_numero_venda(empresa_id: int, sequencia: int) -> str:
    """
    Gera número único de venda no formato: V-{YYYY}-{EMPRESA_ID}-{SEQ}
    
    Args:
        empresa_id: ID da empresa
        sequencia: Número sequencial da venda
    
    Returns:
        str: Número da venda formatado (ex: "V-2026-1-00001")
    
    Examples:
        >>> gerar_numero_venda(1, 1)
        'V-2026-1-00001'
        >>> gerar_numero_venda(5, 123)
        'V-2026-5-00123'
    """
    ano = datetime.now().year
    seq_formatado = str(sequencia).zfill(5)
    return f"V-{ano}-{empresa_id}-{seq_formatado}"
