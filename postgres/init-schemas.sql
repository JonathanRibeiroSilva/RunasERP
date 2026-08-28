-- Script de inicialização do PostgreSQL
-- Cria schemas separados para cada microserviço
-- Executado automaticamente na primeira inicialização do container

-- Criar schemas
CREATE SCHEMA IF NOT EXISTS gateway;
CREATE SCHEMA IF NOT EXISTS empresas;
CREATE SCHEMA IF NOT EXISTS clientes;
CREATE SCHEMA IF NOT EXISTS produtos;
CREATE SCHEMA IF NOT EXISTS estoque;
CREATE SCHEMA IF NOT EXISTS vendas;
CREATE SCHEMA IF NOT EXISTS financeiro;
CREATE SCHEMA IF NOT EXISTS notificacoes;
CREATE SCHEMA IF NOT EXISTS evolution;

-- Garantir permissões para o usuário erp
GRANT ALL ON SCHEMA gateway TO erp;
GRANT ALL ON SCHEMA empresas TO erp;
GRANT ALL ON SCHEMA clientes TO erp;
GRANT ALL ON SCHEMA produtos TO erp;
GRANT ALL ON SCHEMA estoque TO erp;
GRANT ALL ON SCHEMA vendas TO erp;
GRANT ALL ON SCHEMA financeiro TO erp;
GRANT ALL ON SCHEMA notificacoes TO erp;
GRANT ALL ON SCHEMA evolution TO erp;

-- Garantir permissões em objetos futuros
ALTER DEFAULT PRIVILEGES IN SCHEMA gateway GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA empresas GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA clientes GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA produtos GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA estoque GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA vendas GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA financeiro GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA notificacoes GRANT ALL ON TABLES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA evolution GRANT ALL ON TABLES TO erp;

ALTER DEFAULT PRIVILEGES IN SCHEMA gateway GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA empresas GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA clientes GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA produtos GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA estoque GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA vendas GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA financeiro GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA notificacoes GRANT ALL ON SEQUENCES TO erp;
ALTER DEFAULT PRIVILEGES IN SCHEMA evolution GRANT ALL ON SEQUENCES TO erp;

-- Log de sucesso
DO $$
BEGIN
    RAISE NOTICE 'Schemas criados com sucesso: gateway, empresas, clientes, produtos, estoque, vendas, financeiro, notificacoes, evolution';
END $$;

-- ==================== AUDITORIA (Fase 3.2) ====================
-- Mora aqui, e não numa migration de serviço, porque a função de trigger é
-- compartilhada: sete serviços com Alembic independente não têm ordem de boot
-- garantida entre si, e este script roda antes de todos eles. As migrations por
-- serviço só fazem CREATE TRIGGER apontando para esta função.
-- Mantenha em sincronia com o db-init do docker-compose.prod.yml.

-- Nível 1: trilha de intenção, gravada pelo middleware do gateway.
CREATE TABLE IF NOT EXISTS gateway.auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id UUID,
    empresa_id INTEGER,
    metodo VARCHAR(10) NOT NULL,
    rota TEXT NOT NULL,
    payload JSONB,
    status_resposta INTEGER,
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_auditoria_empresa_data
    ON gateway.auditoria (empresa_id, criado_em DESC);

-- Nível 2: snapshot de estado. É o que torna o rollback possível — a trilha
-- diz quem e quando, só o snapshot diz o quê.
CREATE TABLE IF NOT EXISTS gateway.auditoria_registros (
    id BIGSERIAL PRIMARY KEY,
    schema_origem VARCHAR(63) NOT NULL,
    tabela VARCHAR(63) NOT NULL,
    registro_id TEXT,
    empresa_id INTEGER,
    operacao VARCHAR(10) NOT NULL,
    dados_antes JSONB,
    dados_depois JSONB,
    revertido_em TIMESTAMP,
    criado_em TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_auditoria_reg_empresa_data
    ON gateway.auditoria_registros (empresa_id, criado_em DESC);
CREATE INDEX IF NOT EXISTS ix_auditoria_reg_alvo
    ON gateway.auditoria_registros (schema_origem, tabela, registro_id);

CREATE OR REPLACE FUNCTION gateway.auditar_registro() RETURNS trigger AS $fn$
DECLARE
    antes JSONB;
    depois JSONB;
    ref JSONB;
BEGIN
    IF TG_OP <> 'INSERT' THEN antes := to_jsonb(OLD); END IF;
    IF TG_OP <> 'DELETE' THEN depois := to_jsonb(NEW); END IF;
    ref := COALESCE(depois, antes);

    INSERT INTO gateway.auditoria_registros
        (schema_origem, tabela, registro_id, empresa_id, operacao, dados_antes, dados_depois)
    VALUES (
        TG_TABLE_SCHEMA,
        TG_TABLE_NAME,
        ref->>'id',
        -- empresas.empresas não tem coluna empresa_id: ela E a empresa.
        COALESCE(
            (ref->>'empresa_id')::INTEGER,
            CASE WHEN TG_TABLE_SCHEMA = 'empresas' THEN (ref->>'id')::INTEGER END
        ),
        TG_OP,
        antes,
        depois
    );
    RETURN NULL;  -- AFTER trigger: o valor de retorno é ignorado
END;
$fn$ LANGUAGE plpgsql;
