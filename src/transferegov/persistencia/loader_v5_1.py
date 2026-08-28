from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from psycopg.types.json import Jsonb

from transferegov.integracoes.bb.contas import DescobridorContasBB
from transferegov.persistencia.db import conexao
from transferegov.transformacao.f_transferencia import FTransferencia
from transferegov.transformacao.moeda import para_centavos
from transferegov.transformacao.transferencia_operacional import TransferenciaOperacionalExecutor
from transferegov.transformacao.transformador import TransformadorTransferegov


class LoaderV51:
    """Carga idempotente da camada analítica V5.1 no PostgreSQL.

    Regras centrais:
    - valores monetários analíticos são BIGINT em centavos;
    - None permanece NULL;
    - valor federal e valor operacional permanecem lado a lado;
    - movimentações adicionais não viram rendimento automaticamente;
    - saldo BB de conta compartilhada não é atribuído individualmente à TE;
    - toda carga é auditada em transferegov.etl_carga.
    """

    def __init__(
        self,
        caminho_transferegov: str = "dados/transferegov_pmmg.json",
        caminho_bb: str | None = "dados/bb/saldos_investimentos.json",
        esperado_tes: int | None = None,
    ) -> None:
        self.caminho_transferegov = Path(caminho_transferegov)
        self.caminho_bb = Path(caminho_bb) if caminho_bb else None
        self.esperado_tes = esperado_tes

    def executar(self) -> dict[str, Any]:
        bruto, tabelas, transferencias, operacionais, contas, dados_bb = self._preparar()

        if self.esperado_tes is not None and len(transferencias) != self.esperado_tes:
            raise AssertionError(
                f"Quantidade de TEs divergente: esperadas {self.esperado_tes}, "
                f"obtidas {len(transferencias)}. Carga abortada antes do banco."
            )

        observacao = {
            "arquivo_transferegov": str(self.caminho_transferegov),
            "sha256_transferegov": self._sha256(self.caminho_transferegov),
            "arquivo_bb": str(self.caminho_bb) if self.caminho_bb else None,
            "sha256_bb": self._sha256(self.caminho_bb) if self.caminho_bb and self.caminho_bb.exists() else None,
        }

        id_carga = self._iniciar_auditoria(len(bruto), observacao)
        gravados = 0
        try:
            with conexao() as conn:
                with conn.cursor() as cur:
                    mapas = self._mapas_bruto(bruto)
                    for executor in tabelas["executores"]:
                        self._upsert_executor(cur, executor)
                        gravados += 1
                    for te in transferencias:
                        self._upsert_plano(cur, te, mapas)
                        gravados += 1
                    for conta in contas:
                        self._upsert_conta(cur, conta)
                        gravados += 1
                    for conta in contas:
                        for plano in conta.get("planos_acao", []):
                            if plano.get("id_plano_acao") is not None:
                                self._upsert_rel_plano_conta(cur, plano["id_plano_acao"], conta["id_agencia_conta_executor"])
                                gravados += 1
                    op_por_plano = {x.get("id_plano_acao"): x for x in operacionais}
                    for te in transferencias:
                        self._upsert_f_transferencia(cur, te, op_por_plano.get(te.get("id_plano_acao")))
                        gravados += 1
                    for op in operacionais:
                        self._upsert_operacional(cur, op)
                        gravados += 1
                    for mov in tabelas["lancamentos_financeiros"]:
                        self._upsert_movimento(cur, mov)
                        gravados += 1
                    if dados_bb is not None:
                        for registro in dados_bb:
                            gravados += self._upsert_bb(cur, registro)

            self._finalizar_auditoria(id_carga, "OK", gravados, None)
        except Exception as exc:
            self._finalizar_auditoria(id_carga, "ERRO", gravados, str(exc))
            raise

        return {
            "id_carga": id_carga,
            "tes": len(transferencias),
            "executores": len(tabelas["executores"]),
            "contas_executor": len(contas),
            "transferencias_operacionais": len(operacionais),
            "movimentos_gestao_financeira": len(tabelas["lancamentos_financeiros"]),
            "snapshots_bb": 0 if dados_bb is None else len(dados_bb),
            "registros_gravados": gravados,
        }

    def _preparar(self):
        if not self.caminho_transferegov.exists():
            raise FileNotFoundError(self.caminho_transferegov)
        transformador = TransformadorTransferegov(str(self.caminho_transferegov))
        bruto = transformador.carregar_dados()
        tabelas = transformador.normalizar()
        transferencias = FTransferencia(tabelas).construir()
        operacionais = TransferenciaOperacionalExecutor(tabelas).analisar()
        contas = DescobridorContasBB(caminho_origem=str(self.caminho_transferegov)).descobrir()
        dados_bb = None
        if self.caminho_bb is not None and self.caminho_bb.exists():
            with self.caminho_bb.open("r", encoding="utf-8") as arq:
                dados_bb = json.load(arq)
            if not isinstance(dados_bb, list):
                raise ValueError("O JSON BB deve conter uma lista.")
        return bruto, tabelas, transferencias, operacionais, contas, dados_bb

    @staticmethod
    def _mapas_bruto(bruto: list[dict[str, Any]]) -> dict[str, dict[Any, dict[str, Any]]]:
        planos = {}
        executores_por_plano = {}
        for reg in bruto:
            plano = reg.get("plano_acao") or {}
            executor = reg.get("executor") or {}
            pid = plano.get("id_plano_acao")
            if pid is not None:
                planos[pid] = plano
                executores_por_plano[pid] = executor
        return {"planos": planos, "executores_por_plano": executores_por_plano}

    @staticmethod
    def _iniciar_auditoria(registros_lidos: int, observacao: dict[str, Any]) -> int:
        with conexao() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO transferegov.etl_carga
                       (fonte, status, registros_lidos, observacao)
                       VALUES ('TRANSFEREGOV_BB_V5_1','EM_EXECUCAO',%s,%s)
                       RETURNING id_carga""",
                    (registros_lidos, json.dumps(observacao, ensure_ascii=False)),
                )
                return int(cur.fetchone()[0])

    @staticmethod
    def _finalizar_auditoria(id_carga: int, status: str, gravados: int, erro: str | None) -> None:
        """Finaliza a auditoria sem parâmetros SQL de tipo ambíguo.

        PostgreSQL não consegue inferir com segurança o tipo de um parâmetro
        usado apenas em ``%s IS NULL``. Por isso sucesso e erro usam comandos
        explícitos e separados.
        """
        with conexao() as conn:
            with conn.cursor() as cur:
                if erro is None:
                    cur.execute(
                        """UPDATE transferegov.etl_carga
                           SET finalizado_em=NOW(),
                               status=%s,
                               registros_gravados=%s
                           WHERE id_carga=%s""",
                        (status, gravados, id_carga),
                    )
                else:
                    cur.execute(
                        """UPDATE transferegov.etl_carga
                           SET finalizado_em=NOW(),
                               status=%s,
                               registros_gravados=%s,
                               observacao=COALESCE(observacao,'') || E'\\nERRO: ' || %s::text
                           WHERE id_carga=%s""",
                        (status, gravados, erro, id_carga),
                    )

    @staticmethod
    def _upsert_executor(cur, x: dict[str, Any]) -> None:
        cur.execute("""INSERT INTO transferegov.dim_executor
            (id_executor,cnpj_executor,nome_executor,codigo_banco_executor,numero_agencia_executor,
             dv_agencia_executor,numero_conta_executor,dv_conta_executor,situacao_conta_executor)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_executor) DO UPDATE SET
            cnpj_executor=EXCLUDED.cnpj_executor,nome_executor=EXCLUDED.nome_executor,
            codigo_banco_executor=EXCLUDED.codigo_banco_executor,numero_agencia_executor=EXCLUDED.numero_agencia_executor,
            dv_agencia_executor=EXCLUDED.dv_agencia_executor,numero_conta_executor=EXCLUDED.numero_conta_executor,
            dv_conta_executor=EXCLUDED.dv_conta_executor,situacao_conta_executor=EXCLUDED.situacao_conta_executor,
            atualizado_em=NOW()""", (
            x.get("id_executor"), x.get("cnpj_executor"), x.get("nome_executor"), x.get("codigo_banco_executor"),
            x.get("numero_agencia_executor"), x.get("numero_dv_agencia_executor"), x.get("numero_conta_executor"),
            x.get("numero_dv_conta_executor"), x.get("descricao_situacao_dado_bancario_executor")))

    @staticmethod
    def _upsert_plano(cur, te: dict[str, Any], mapas: dict[str, Any]) -> None:
        pid = te.get("id_plano_acao")
        plano = mapas["planos"].get(pid, {})
        executor = mapas["executores_por_plano"].get(pid, {})
        cur.execute("""INSERT INTO transferegov.dim_plano_acao
            (id_plano_acao,codigo_plano_acao,ano_plano_acao,situacao_plano_acao,nome_parlamentar,numero_emenda,
             codigo_emenda_formatado,nome_objeto,detalhamento_objeto,categoria_despesa,id_programa,id_beneficiario,id_executor,id_agencia_conta_plano)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_plano_acao) DO UPDATE SET
            codigo_plano_acao=EXCLUDED.codigo_plano_acao,ano_plano_acao=EXCLUDED.ano_plano_acao,
            situacao_plano_acao=EXCLUDED.situacao_plano_acao,nome_parlamentar=EXCLUDED.nome_parlamentar,
            numero_emenda=EXCLUDED.numero_emenda,codigo_emenda_formatado=EXCLUDED.codigo_emenda_formatado,
            nome_objeto=EXCLUDED.nome_objeto,detalhamento_objeto=EXCLUDED.detalhamento_objeto,
            categoria_despesa=EXCLUDED.categoria_despesa,id_programa=EXCLUDED.id_programa,
            id_beneficiario=EXCLUDED.id_beneficiario,id_executor=EXCLUDED.id_executor,
            id_agencia_conta_plano=EXCLUDED.id_agencia_conta_plano,atualizado_em=NOW()""", (
            pid, te.get("codigo_plano_acao"), te.get("ano_plano_acao"), te.get("situacao_plano_acao"), te.get("nome_parlamentar"),
            te.get("numero_emenda"), te.get("codigo_emenda_formatado"), te.get("nome_objeto"), te.get("detalhamento_objeto"),
            te.get("categoria_despesa"), te.get("id_programa"), te.get("id_beneficiario"), executor.get("id_executor"), plano.get("id_agencia_conta")))

    @staticmethod
    def _upsert_conta(cur, x: dict[str, Any]) -> None:
        cur.execute("""INSERT INTO transferegov.dim_conta_executor
            (id_agencia_conta_executor,codigo_banco,agencia,dv_agencia,conta,dv_conta,situacao,quantidade_planos_acao,
             conta_compartilhada,conta_exclusiva_te,origem_conta_consulta_bb)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_agencia_conta_executor) DO UPDATE SET
            codigo_banco=EXCLUDED.codigo_banco,agencia=EXCLUDED.agencia,dv_agencia=EXCLUDED.dv_agencia,
            conta=EXCLUDED.conta,dv_conta=EXCLUDED.dv_conta,situacao=EXCLUDED.situacao,
            quantidade_planos_acao=EXCLUDED.quantidade_planos_acao,conta_compartilhada=EXCLUDED.conta_compartilhada,
            conta_exclusiva_te=EXCLUDED.conta_exclusiva_te,origem_conta_consulta_bb=EXCLUDED.origem_conta_consulta_bb,
            atualizado_em=NOW()""", (x.get("id_agencia_conta_executor"),x.get("codigo_banco"),x.get("agencia"),x.get("dv_agencia"),x.get("conta"),x.get("dv_conta"),x.get("situacao"),x.get("quantidade_planos_acao"),x.get("conta_compartilhada"),x.get("conta_exclusiva_te"),x.get("origem_conta_consulta_bb")))

    @staticmethod
    def _upsert_rel_plano_conta(cur, pid: int, cid: str) -> None:
        cur.execute("""INSERT INTO transferegov.rel_plano_conta_executor (id_plano_acao,id_agencia_conta_executor)
                       VALUES (%s,%s) ON CONFLICT DO NOTHING""", (pid,cid))

    @staticmethod
    def _upsert_f_transferencia(cur, te: dict[str, Any], op: dict[str, Any] | None) -> None:
        op = op or {}
        cur.execute("""INSERT INTO transferegov.f_transferencia (
            id_plano_acao,valor_destinado_centavos,valor_custeio_centavos,valor_investimento_centavos,
            valor_transferido_federal_centavos,valor_transferido_operacional_centavos,valor_movimentacoes_adicionais_executor_centavos,
            valor_rendimentos_centavos,recursos_disponiveis_centavos,valor_empenhado_centavos,valor_liquidado_centavos,valor_pago_centavos,
            valor_executado_centavos,liquidado_a_pagar_centavos,saldo_financeiro_teorico_centavos,valor_a_executar_centavos,percentual_execucao,
            saldo_conta_transferegov_centavos,data_saldo_transferegov,origem_valor_transferido_federal,origem_valor_transferido_operacional,
            status_transferencia_operacional,verificacao_manual_transferencia_operacional,quantidade_movimentacoes_adicionais,
            tem_movimentacao_adicional_executor,verificacao_manual_movimentacao_adicional,conta_compartilhada_transferegov,
            conta_exclusiva_te_transferegov,saldo_conta_te_confiavel,quantidade_planos_trabalho,quantidade_planos_aprovados,teve_complementacao,
            quantidade_metas,quantidade_analises,quantidade_orgaos_analisadores,multiplos_orgaos_analisadores,quantidade_relatorios_gestao,
            tem_relatorio_gestao,tem_relatorio_novo,tem_relatorio_legado)
            VALUES (""" + ",".join(["%s"]*40) + ") ON CONFLICT (id_plano_acao) DO UPDATE SET " +
            ",".join([f"{c}=EXCLUDED.{c}" for c in [
                "valor_destinado_centavos","valor_custeio_centavos","valor_investimento_centavos","valor_transferido_federal_centavos",
                "valor_transferido_operacional_centavos","valor_movimentacoes_adicionais_executor_centavos","valor_rendimentos_centavos",
                "recursos_disponiveis_centavos","valor_empenhado_centavos","valor_liquidado_centavos","valor_pago_centavos","valor_executado_centavos",
                "liquidado_a_pagar_centavos","saldo_financeiro_teorico_centavos","valor_a_executar_centavos","percentual_execucao",
                "saldo_conta_transferegov_centavos","data_saldo_transferegov","origem_valor_transferido_federal","origem_valor_transferido_operacional",
                "status_transferencia_operacional","verificacao_manual_transferencia_operacional","quantidade_movimentacoes_adicionais",
                "tem_movimentacao_adicional_executor","verificacao_manual_movimentacao_adicional","conta_compartilhada_transferegov",
                "conta_exclusiva_te_transferegov","saldo_conta_te_confiavel","quantidade_planos_trabalho","quantidade_planos_aprovados",
                "teve_complementacao","quantidade_metas","quantidade_analises","quantidade_orgaos_analisadores","multiplos_orgaos_analisadores",
                "quantidade_relatorios_gestao","tem_relatorio_gestao","tem_relatorio_novo","tem_relatorio_legado"]]) + ",atualizado_em=NOW()", (
            te.get("id_plano_acao"),te.get("valor_destinado_centavos"),te.get("valor_custeio_centavos"),te.get("valor_investimento_centavos"),
            te.get("valor_transferido_centavos"),op.get("valor_transferido_operacional_centavos"),op.get("valor_movimentacoes_adicionais_executor_centavos"),
            te.get("valor_rendimentos_centavos"),te.get("recursos_disponiveis_centavos"),te.get("valor_empenhado_centavos"),te.get("valor_liquidado_centavos"),
            te.get("valor_pago_centavos"),te.get("valor_executado_centavos"),te.get("liquidado_a_pagar_centavos"),te.get("saldo_financeiro_teorico_centavos"),
            te.get("valor_a_executar_centavos"),te.get("percentual_execucao"),te.get("saldo_conta_centavos"),LoaderV51._date(te.get("data_saldo")),
            te.get("origem_valor_transferido"),op.get("origem_valor_transferido_operacional"),op.get("status_transferencia_operacional"),
            op.get("verificacao_manual_transferencia_operacional"),op.get("quantidade_movimentacoes_adicionais"),op.get("tem_movimentacao_adicional_executor"),
            op.get("verificacao_manual_movimentacao_adicional"),te.get("conta_compartilhada"),te.get("conta_exclusiva_te"),te.get("saldo_conta_te_confiavel"),
            te.get("quantidade_planos_trabalho"),te.get("quantidade_planos_aprovados"),te.get("teve_complementacao"),te.get("quantidade_metas"),
            te.get("quantidade_analises"),te.get("quantidade_orgaos_analisadores"),te.get("multiplos_orgaos_analisadores"),te.get("quantidade_relatorios_gestao"),
            te.get("tem_relatorio_gestao"),te.get("tem_relatorio_novo"),te.get("tem_relatorio_legado")))

    @staticmethod
    def _upsert_operacional(cur, x: dict[str, Any]) -> None:
        cur.execute("""INSERT INTO transferegov.f_transferencia_operacional
            (id_plano_acao,id_executor,id_agencia_conta_executor,referencia_bb_esperada,valor_previsto_executor_centavos,
             valor_transferido_operacional_centavos,valor_movimentacoes_adicionais_executor_centavos,quantidade_transferencias_candidatas,
             quantidade_movimentacoes_adicionais,status_transferencia_operacional,origem_valor_transferido_operacional,
             verificacao_manual_transferencia_operacional,tem_movimentacao_adicional_executor,verificacao_manual_movimentacao_adicional,
             ids_lancamentos_principal,ids_lancamentos_adicionais)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_plano_acao) DO UPDATE SET
            id_executor=EXCLUDED.id_executor,id_agencia_conta_executor=EXCLUDED.id_agencia_conta_executor,
            referencia_bb_esperada=EXCLUDED.referencia_bb_esperada,valor_previsto_executor_centavos=EXCLUDED.valor_previsto_executor_centavos,
            valor_transferido_operacional_centavos=EXCLUDED.valor_transferido_operacional_centavos,
            valor_movimentacoes_adicionais_executor_centavos=EXCLUDED.valor_movimentacoes_adicionais_executor_centavos,
            quantidade_transferencias_candidatas=EXCLUDED.quantidade_transferencias_candidatas,
            quantidade_movimentacoes_adicionais=EXCLUDED.quantidade_movimentacoes_adicionais,status_transferencia_operacional=EXCLUDED.status_transferencia_operacional,
            origem_valor_transferido_operacional=EXCLUDED.origem_valor_transferido_operacional,
            verificacao_manual_transferencia_operacional=EXCLUDED.verificacao_manual_transferencia_operacional,
            tem_movimentacao_adicional_executor=EXCLUDED.tem_movimentacao_adicional_executor,
            verificacao_manual_movimentacao_adicional=EXCLUDED.verificacao_manual_movimentacao_adicional,
            ids_lancamentos_principal=EXCLUDED.ids_lancamentos_principal,ids_lancamentos_adicionais=EXCLUDED.ids_lancamentos_adicionais,atualizado_em=NOW()""", (
            x.get("id_plano_acao"),x.get("id_executor"),x.get("id_agencia_conta_executor"),x.get("referencia_bb_esperada"),
            x.get("valor_previsto_executor_centavos"),x.get("valor_transferido_operacional_centavos"),x.get("valor_movimentacoes_adicionais_executor_centavos"),
            x.get("quantidade_transferencias_candidatas"),x.get("quantidade_movimentacoes_adicionais"),x.get("status_transferencia_operacional"),
            x.get("origem_valor_transferido_operacional"),bool(x.get("verificacao_manual_transferencia_operacional")),x.get("tem_movimentacao_adicional_executor"),
            bool(x.get("verificacao_manual_movimentacao_adicional")),Jsonb(x.get("ids_lancamentos_principal") or []),Jsonb(x.get("ids_lancamentos_adicionais") or [])))

    @staticmethod
    def _upsert_movimento(cur, x: dict[str, Any]) -> None:
        lid = x.get("id_lancamento_gestao_financeira")
        if lid is None:
            return
        cur.execute("""INSERT INTO transferegov.f_movimento_gestao_financeira
            (id_lancamento_gestao_financeira,id_plano_acao,id_agencia_conta_plano,descricao,data_lancamento,numero_ordem,
             numero_referencia_unica,tipo_operacao,valor_centavos,doc_favorecido,nome_favorecido,codigo_banco_favorecido)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_lancamento_gestao_financeira) DO UPDATE SET
            id_plano_acao=EXCLUDED.id_plano_acao,id_agencia_conta_plano=EXCLUDED.id_agencia_conta_plano,descricao=EXCLUDED.descricao,
            data_lancamento=EXCLUDED.data_lancamento,numero_ordem=EXCLUDED.numero_ordem,numero_referencia_unica=EXCLUDED.numero_referencia_unica,
            tipo_operacao=EXCLUDED.tipo_operacao,valor_centavos=EXCLUDED.valor_centavos,doc_favorecido=EXCLUDED.doc_favorecido,
            nome_favorecido=EXCLUDED.nome_favorecido,codigo_banco_favorecido=EXCLUDED.codigo_banco_favorecido,atualizado_em=NOW()""", (
            str(lid),x.get("id_plano_acao"),x.get("id_agencia_conta"),x.get("descricao_gestao_financeira"),LoaderV51._date(x.get("data_lancamento_gestao_financeira")),
            x.get("numero_ordem_gestao_financeira"),x.get("numero_referencia_unica_gestao_financeira"),x.get("tipo_operacao_gestao_financeira"),
            para_centavos(x.get("valor_gestao_financeira")),x.get("doc_favorecido_gestao_financeira"),x.get("nome_favorecido_gestao_financeira"),x.get("codigo_banco_favorecido_gestao_financeira")))

    @staticmethod
    def _upsert_bb(cur, r: dict[str, Any]) -> int:
        cid = r.get("id_agencia_conta_executor")
        if not cid:
            return 0
        consultado = LoaderV51._datetime(r.get("consultado_em"))
        if consultado is None:
            raise ValueError(f"Snapshot BB sem consultado_em para conta {cid}")
        cur.execute("""INSERT INTO transferegov.f_bb_saldo_conta
            (id_agencia_conta_executor,consultado_em,status_consulta,verificacao_manual_bb,status_http_bb,codigo_erro_api_bb,
             mensagem_erro_api_bb,quantidade_fundos,saldo_investimento_bb_conta_centavos,dados_fundos,detalhes_erro_api_bb)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id_agencia_conta_executor,consultado_em) DO UPDATE SET
            status_consulta=EXCLUDED.status_consulta,verificacao_manual_bb=EXCLUDED.verificacao_manual_bb,status_http_bb=EXCLUDED.status_http_bb,
            codigo_erro_api_bb=EXCLUDED.codigo_erro_api_bb,mensagem_erro_api_bb=EXCLUDED.mensagem_erro_api_bb,
            quantidade_fundos=EXCLUDED.quantidade_fundos,saldo_investimento_bb_conta_centavos=EXCLUDED.saldo_investimento_bb_conta_centavos,
            dados_fundos=EXCLUDED.dados_fundos,detalhes_erro_api_bb=EXCLUDED.detalhes_erro_api_bb
            RETURNING id_bb_saldo""", (
            cid,consultado,r.get("status_consulta") or "NAO_DISPONIVEL",bool(r.get("verificacao_manual_bb")),r.get("status_http_bb"),
            r.get("codigo_erro_api_bb"),r.get("mensagem_erro_api_bb"),r.get("quantidade_fundos"),r.get("saldo_investimento_bb_centavos"),
            Jsonb(r.get("fundos")) if r.get("fundos") is not None else None,Jsonb(r.get("detalhes_erro_api_bb")) if r.get("detalhes_erro_api_bb") is not None else None))
        id_bb = int(cur.fetchone()[0])
        planos = r.get("planos_acao") or []
        qtd = r.get("quantidade_planos_acao")
        if qtd is None: qtd = len(planos)
        compartilhada = int(qtd or 0) > 1
        status = r.get("status_consulta")
        saldo_conta = r.get("saldo_investimento_bb_centavos")
        manual = bool(r.get("verificacao_manual_bb")) or status not in {"OK","SEM_FUNDOS"}
        count = 1
        for p in planos:
            pid = p.get("id_plano_acao")
            if pid is None: continue
            if status not in {"OK","SEM_FUNDOS"}:
                atribuivel, saldo_te, motivo = False, None, "DADOS_BB_INDISPONIVEIS"
            elif status == "SEM_FUNDOS":
                atribuivel, saldo_te, motivo = False, None, "SEM_FUNDOS"
            elif compartilhada:
                atribuivel, saldo_te, motivo = False, None, "CONTA_EXECUTOR_COMPARTILHADA"
            else:
                atribuivel, saldo_te, motivo = True, saldo_conta, None
            cur.execute("""INSERT INTO transferegov.f_bb_saldo_te
                (id_plano_acao,id_bb_saldo,saldo_investimento_bb_centavos,saldo_bb_atribuivel_te,motivo_saldo_nao_atribuido,
                 status_dados_bb,verificacao_manual_bb,codigo_erro_api_bb)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id_plano_acao,id_bb_saldo) DO UPDATE SET
                saldo_investimento_bb_centavos=EXCLUDED.saldo_investimento_bb_centavos,
                saldo_bb_atribuivel_te=EXCLUDED.saldo_bb_atribuivel_te,motivo_saldo_nao_atribuido=EXCLUDED.motivo_saldo_nao_atribuido,
                status_dados_bb=EXCLUDED.status_dados_bb,verificacao_manual_bb=EXCLUDED.verificacao_manual_bb,
                codigo_erro_api_bb=EXCLUDED.codigo_erro_api_bb""", (pid,id_bb,saldo_te,atribuivel,motivo,status,manual,r.get("codigo_erro_api_bb")))
            count += 1
        return count

    @staticmethod
    def _date(v: Any) -> date | None:
        if v is None or v == "": return None
        if isinstance(v, datetime): return v.date()
        if isinstance(v, date): return v
        return date.fromisoformat(str(v)[:10])

    @staticmethod
    def _datetime(v: Any) -> datetime | None:
        if v is None or v == "": return None
        if isinstance(v, datetime): return v
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as arq:
            for bloco in iter(lambda: arq.read(1024 * 1024), b""):
                h.update(bloco)
        return h.hexdigest()
