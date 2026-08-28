BEGIN;

CREATE SCHEMA IF NOT EXISTS transferegov;

CREATE TABLE IF NOT EXISTS transferegov.etl_carga (
    id_carga BIGSERIAL PRIMARY KEY,
    fonte VARCHAR(50) NOT NULL,
    iniciado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizado_em TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'EM_EXECUCAO',
    registros_lidos INTEGER,
    registros_gravados INTEGER,
    observacao TEXT,
    CONSTRAINT ck_etl_carga_status
        CHECK (status IN ('EM_EXECUCAO', 'OK', 'ERRO'))
);

CREATE TABLE IF NOT EXISTS transferegov.dim_executor (
    id_executor BIGINT PRIMARY KEY,
    cnpj_executor VARCHAR(14),
    nome_executor TEXT,
    codigo_banco_executor VARCHAR(10),
    numero_agencia_executor VARCHAR(20),
    dv_agencia_executor VARCHAR(5),
    numero_conta_executor VARCHAR(30),
    dv_conta_executor VARCHAR(5),
    situacao_conta_executor TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- A mesma pessoa jurídica/conta pode aparecer com vários id_executor
-- de origem no Transferegov. Portanto este índice é apenas de consulta,
-- não uma restrição de unicidade.
CREATE INDEX IF NOT EXISTS ix_dim_executor_cnpj_conta
ON transferegov.dim_executor (
    cnpj_executor,
    numero_agencia_executor,
    numero_conta_executor
)
WHERE cnpj_executor IS NOT NULL
  AND numero_agencia_executor IS NOT NULL
  AND numero_conta_executor IS NOT NULL;

CREATE TABLE IF NOT EXISTS transferegov.dim_plano_acao (
    id_plano_acao BIGINT PRIMARY KEY,
    codigo_plano_acao TEXT,
    ano_plano_acao INTEGER,
    situacao_plano_acao TEXT,
    nome_parlamentar TEXT,
    numero_emenda TEXT,
    codigo_emenda_formatado TEXT,
    nome_objeto TEXT,
    detalhamento_objeto TEXT,
    categoria_despesa TEXT,
    id_programa BIGINT,
    id_beneficiario BIGINT,
    id_executor BIGINT,
    id_agencia_conta_plano TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_plano_executor
        FOREIGN KEY (id_executor)
        REFERENCES transferegov.dim_executor(id_executor)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_plano_acao_codigo
ON transferegov.dim_plano_acao (codigo_plano_acao)
WHERE codigo_plano_acao IS NOT NULL;

CREATE TABLE IF NOT EXISTS transferegov.dim_conta_executor (
    id_agencia_conta_executor TEXT PRIMARY KEY,
    codigo_banco VARCHAR(10),
    agencia VARCHAR(20) NOT NULL,
    dv_agencia VARCHAR(5),
    conta VARCHAR(30) NOT NULL,
    dv_conta VARCHAR(5),
    situacao TEXT,
    quantidade_planos_acao INTEGER,
    conta_compartilhada BOOLEAN,
    conta_exclusiva_te BOOLEAN,
    origem_conta_consulta_bb TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transferegov.rel_plano_conta_executor (
    id_plano_acao BIGINT NOT NULL,
    id_agencia_conta_executor TEXT NOT NULL,
    PRIMARY KEY (id_plano_acao, id_agencia_conta_executor),
    CONSTRAINT fk_rel_plano
        FOREIGN KEY (id_plano_acao)
        REFERENCES transferegov.dim_plano_acao(id_plano_acao)
        ON DELETE CASCADE,
    CONSTRAINT fk_rel_conta
        FOREIGN KEY (id_agencia_conta_executor)
        REFERENCES transferegov.dim_conta_executor(id_agencia_conta_executor)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transferegov.f_transferencia (
    id_plano_acao BIGINT PRIMARY KEY,

    valor_destinado_centavos BIGINT,
    valor_custeio_centavos BIGINT,
    valor_investimento_centavos BIGINT,

    valor_transferido_federal_centavos BIGINT,
    valor_transferido_operacional_centavos BIGINT,
    valor_movimentacoes_adicionais_executor_centavos BIGINT,

    valor_rendimentos_centavos BIGINT,
    recursos_disponiveis_centavos BIGINT,

    valor_empenhado_centavos BIGINT,
    valor_liquidado_centavos BIGINT,
    valor_pago_centavos BIGINT,
    valor_executado_centavos BIGINT,
    liquidado_a_pagar_centavos BIGINT,
    saldo_financeiro_teorico_centavos BIGINT,
    valor_a_executar_centavos BIGINT,

    percentual_execucao NUMERIC(20,10),

    saldo_conta_transferegov_centavos BIGINT,
    data_saldo_transferegov DATE,

    origem_valor_transferido_federal TEXT,
    origem_valor_transferido_operacional TEXT,
    status_transferencia_operacional TEXT,
    verificacao_manual_transferencia_operacional BOOLEAN,

    quantidade_movimentacoes_adicionais INTEGER,
    tem_movimentacao_adicional_executor BOOLEAN,
    verificacao_manual_movimentacao_adicional BOOLEAN,

    conta_compartilhada_transferegov BOOLEAN,
    conta_exclusiva_te_transferegov BOOLEAN,
    saldo_conta_te_confiavel BOOLEAN,

    quantidade_planos_trabalho INTEGER,
    quantidade_planos_aprovados INTEGER,
    teve_complementacao BOOLEAN,
    quantidade_metas INTEGER,
    quantidade_analises INTEGER,
    quantidade_orgaos_analisadores INTEGER,
    multiplos_orgaos_analisadores BOOLEAN,
    quantidade_relatorios_gestao INTEGER,
    tem_relatorio_gestao BOOLEAN,
    tem_relatorio_novo BOOLEAN,
    tem_relatorio_legado BOOLEAN,

    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_f_transferencia_plano
        FOREIGN KEY (id_plano_acao)
        REFERENCES transferegov.dim_plano_acao(id_plano_acao)
        ON DELETE CASCADE,

    CONSTRAINT ck_percentual_execucao
        CHECK (
            percentual_execucao IS NULL
            OR percentual_execucao >= 0
        )
);

CREATE TABLE IF NOT EXISTS transferegov.f_transferencia_operacional (
    id_plano_acao BIGINT PRIMARY KEY,
    id_executor BIGINT,
    id_agencia_conta_executor TEXT,
    referencia_bb_esperada TEXT,

    valor_previsto_executor_centavos BIGINT,
    valor_transferido_operacional_centavos BIGINT,
    valor_movimentacoes_adicionais_executor_centavos BIGINT,

    quantidade_transferencias_candidatas INTEGER,
    quantidade_movimentacoes_adicionais INTEGER,

    status_transferencia_operacional TEXT NOT NULL,
    origem_valor_transferido_operacional TEXT,
    verificacao_manual_transferencia_operacional BOOLEAN NOT NULL,
    tem_movimentacao_adicional_executor BOOLEAN,
    verificacao_manual_movimentacao_adicional BOOLEAN,

    ids_lancamentos_principal JSONB NOT NULL DEFAULT '[]'::jsonb,
    ids_lancamentos_adicionais JSONB NOT NULL DEFAULT '[]'::jsonb,

    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_f_operacional_plano
        FOREIGN KEY (id_plano_acao)
        REFERENCES transferegov.dim_plano_acao(id_plano_acao)
        ON DELETE CASCADE,

    CONSTRAINT fk_f_operacional_executor
        FOREIGN KEY (id_executor)
        REFERENCES transferegov.dim_executor(id_executor),

    CONSTRAINT fk_f_operacional_conta
        FOREIGN KEY (id_agencia_conta_executor)
        REFERENCES transferegov.dim_conta_executor(id_agencia_conta_executor)
);

CREATE TABLE IF NOT EXISTS transferegov.f_bb_saldo_conta (
    id_bb_saldo BIGSERIAL PRIMARY KEY,
    id_agencia_conta_executor TEXT NOT NULL,
    consultado_em TIMESTAMPTZ NOT NULL,

    status_consulta VARCHAR(30) NOT NULL,
    verificacao_manual_bb BOOLEAN NOT NULL,

    status_http_bb INTEGER,
    codigo_erro_api_bb TEXT,
    mensagem_erro_api_bb TEXT,

    quantidade_fundos INTEGER,
    saldo_investimento_bb_conta_centavos BIGINT,

    dados_fundos JSONB,
    detalhes_erro_api_bb JSONB,

    CONSTRAINT fk_bb_saldo_conta
        FOREIGN KEY (id_agencia_conta_executor)
        REFERENCES transferegov.dim_conta_executor(id_agencia_conta_executor),

    CONSTRAINT ux_bb_saldo_snapshot
        UNIQUE (id_agencia_conta_executor, consultado_em)
);

CREATE INDEX IF NOT EXISTS ix_bb_saldo_conta_data
ON transferegov.f_bb_saldo_conta (
    id_agencia_conta_executor,
    consultado_em DESC
);

CREATE TABLE IF NOT EXISTS transferegov.f_bb_saldo_te (
    id_plano_acao BIGINT NOT NULL,
    id_bb_saldo BIGINT NOT NULL,

    saldo_investimento_bb_centavos BIGINT,
    saldo_bb_atribuivel_te BOOLEAN NOT NULL DEFAULT FALSE,
    motivo_saldo_nao_atribuido TEXT,
    status_dados_bb TEXT,
    verificacao_manual_bb BOOLEAN,
    codigo_erro_api_bb TEXT,

    PRIMARY KEY (id_plano_acao, id_bb_saldo),

    CONSTRAINT fk_bb_te_plano
        FOREIGN KEY (id_plano_acao)
        REFERENCES transferegov.dim_plano_acao(id_plano_acao)
        ON DELETE CASCADE,

    CONSTRAINT fk_bb_te_saldo
        FOREIGN KEY (id_bb_saldo)
        REFERENCES transferegov.f_bb_saldo_conta(id_bb_saldo)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transferegov.f_movimento_gestao_financeira (
    id_lancamento_gestao_financeira TEXT PRIMARY KEY,
    id_plano_acao BIGINT NOT NULL,
    id_agencia_conta_plano TEXT,

    descricao TEXT,
    data_lancamento DATE,
    numero_ordem INTEGER,
    numero_referencia_unica TEXT,
    tipo_operacao VARCHAR(5),
    valor_centavos BIGINT,

    doc_favorecido TEXT,
    nome_favorecido TEXT,
    codigo_banco_favorecido TEXT,

    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_movimento_plano
        FOREIGN KEY (id_plano_acao)
        REFERENCES transferegov.dim_plano_acao(id_plano_acao)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_movimento_plano_data
ON transferegov.f_movimento_gestao_financeira (
    id_plano_acao,
    data_lancamento
);

COMMENT ON SCHEMA transferegov IS
'Camada analítica do projeto Transferegov PMMG para consumo posterior pelo Power BI.';

COMMENT ON COLUMN transferegov.f_transferencia.valor_transferido_federal_centavos IS
'Valor confirmado pela cadeia federal Empenho -> Documento Hábil -> OP/OB. BIGINT em centavos.';

COMMENT ON COLUMN transferegov.f_transferencia.valor_transferido_operacional_centavos IS
'Valor confirmado na gestão financeira como transferência para a conta executor da PMMG. BIGINT em centavos.';

COMMENT ON COLUMN transferegov.f_transferencia.valor_movimentacoes_adicionais_executor_centavos IS
'Movimentações adicionais para a conta executor. Não classificadas automaticamente como rendimento. BIGINT em centavos.';

COMMENT ON COLUMN transferegov.f_bb_saldo_conta.saldo_investimento_bb_conta_centavos IS
'Saldo observado no nível da conta executor. Em conta compartilhada não deve ser somado por TE.';

COMMIT;
