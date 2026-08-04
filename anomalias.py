import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from config import MESES
from parametros import validar_parametros


def _classificar_razao(razao, p):
    condicoes = [
        razao < p.muito_abaixo,
        razao < p.abaixo,
        razao < p.ligeiramente_abaixo,
        razao <= p.proximo_superior,
        razao <= p.ligeiramente_acima,
        razao <= p.muito_acima,
        razao > p.muito_acima,
    ]
    classes = [
        "MUITO_ABAIXO",
        "ABAIXO",
        "LIGEIRAMENTE_ABAIXO",
        "PROXIMO_DA_NORMAL",
        "LIGEIRAMENTE_ACIMA",
        "ACIMA",
        "MUITO_ACIMA",
    ]
    return np.select(condicoes, classes, default="NAO_CLASSIFICADO")


def processar_anomalias(resultado_observados, arquivo_climatologia, pasta_saida, parametros):
    erros = validar_parametros(parametros)
    if erros:
        raise ValueError("\n".join(erros))
    if not resultado_observados or not resultado_observados.get("conjunto_valido"):
        raise ValueError("Os dados observados precisam ser validados antes do processamento.")

    arquivo_climatologia = Path(arquivo_climatologia)
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    observados = pd.concat(
        [item["dataframe"].copy() for item in resultado_observados["arquivos"]],
        ignore_index=True,
    )
    observados["ano"] = observados["ano"].astype("int16")
    observados["mes"] = observados["mes"].astype("int8")

    climatologia = pd.read_csv(
        arquivo_climatologia,
        encoding="utf-8-sig",
        dtype={"cd_mun": "string"},
        low_memory=False,
    )
    climatologia["mes"] = pd.to_numeric(climatologia["mes"], errors="raise").astype("int8")
    climatologia["normal_mm"] = pd.to_numeric(climatologia["normal_mm"], errors="coerce")

    clima_merge = climatologia[
        ["cd_mun", "mes", "normal_mm", "status_dados", "periodo_referencia", "malha_municipal"]
    ].rename(columns={"status_dados": "status_climatologia"})

    mensal = observados.merge(
        clima_merge,
        on=["cd_mun", "mes"],
        how="left",
        validate="many_to_one",
        indicator=True,
    )
    if (mensal["_merge"] != "both").any():
        raise ValueError("Existem registros observados sem correspondência na climatologia.")
    mensal = mensal.drop(columns="_merge")

    mensal["nome_mes"] = mensal["mes"].map(MESES)
    mensal["anomalia_mm"] = mensal["precipitacao_mm"] - mensal["normal_mm"]

    apta = (
        mensal["precipitacao_mm"].notna()
        & mensal["normal_mm"].notna()
        & mensal["normal_mm"].ge(parametros.limiar_normal_mm)
    )
    mensal["razao_normal"] = np.where(
        apta, mensal["precipitacao_mm"] / mensal["normal_mm"], np.nan
    )
    mensal["anomalia_pct"] = np.where(
        apta, 100.0 * mensal["anomalia_mm"] / mensal["normal_mm"], np.nan
    )

    mensal["status_calculo"] = np.select(
        [
            mensal["precipitacao_mm"].isna(),
            mensal["normal_mm"].isna(),
            mensal["normal_mm"].lt(parametros.limiar_normal_mm),
        ],
        ["SEM_DADO_OBSERVADO", "SEM_NORMAL_CLIMATOLOGICA", "NORMAL_MUITO_BAIXA"],
        default="CALCULADO",
    )
    mensal["classificacao"] = mensal["status_calculo"]
    mensal.loc[apta, "classificacao"] = _classificar_razao(
        mensal.loc[apta, "razao_normal"], parametros
    )

    colunas_mensais = [
        "cd_mun", "nm_mun", "sigla_uf", "area_km2", "ano", "mes", "nome_mes",
        "data", "precipitacao_mm", "normal_mm", "anomalia_mm", "anomalia_pct",
        "razao_normal", "classificacao", "status_calculo", "status_climatologia",
        "fonte", "periodo_referencia", "malha_municipal",
    ]
    mensal = mensal[colunas_mensais].sort_values(["cd_mun", "ano", "mes"]).reset_index(drop=True)

    chaves = ["cd_mun", "nm_mun", "sigla_uf", "area_km2", "ano"]
    resumo_anual = mensal.groupby(chaves, dropna=False).agg(
        meses_observados_validos=("precipitacao_mm", "count"),
        meses_normais_validos=("normal_mm", "count"),
        precipitacao_anual_mm=("precipitacao_mm", lambda x: x.sum(min_count=12)),
        normal_anual_mm=("normal_mm", lambda x: x.sum(min_count=12)),
        meses_muito_abaixo=("classificacao", lambda x: int((x == "MUITO_ABAIXO").sum())),
        meses_abaixo=("classificacao", lambda x: int(x.isin(["MUITO_ABAIXO", "ABAIXO", "LIGEIRAMENTE_ABAIXO"]).sum())),
        meses_proximos_normal=("classificacao", lambda x: int((x == "PROXIMO_DA_NORMAL").sum())),
        meses_acima=("classificacao", lambda x: int(x.isin(["LIGEIRAMENTE_ACIMA", "ACIMA", "MUITO_ACIMA"]).sum())),
        meses_muito_acima=("classificacao", lambda x: int((x == "MUITO_ACIMA").sum())),
    ).reset_index()

    resumo_anual["anomalia_anual_mm"] = resumo_anual["precipitacao_anual_mm"] - resumo_anual["normal_anual_mm"]
    anual_apta = resumo_anual["precipitacao_anual_mm"].notna() & resumo_anual["normal_anual_mm"].gt(0)
    resumo_anual["razao_normal_anual"] = np.where(
        anual_apta, resumo_anual["precipitacao_anual_mm"] / resumo_anual["normal_anual_mm"], np.nan
    )
    resumo_anual["anomalia_anual_pct"] = np.where(
        anual_apta, 100.0 * resumo_anual["anomalia_anual_mm"] / resumo_anual["normal_anual_mm"], np.nan
    )
    resumo_anual["classificacao_anual"] = "INCOMPLETA"
    resumo_anual.loc[anual_apta, "classificacao_anual"] = _classificar_razao(
        resumo_anual.loc[anual_apta, "razao_normal_anual"], parametros
    )

    resumo_uf = (
        mensal.loc[mensal["status_calculo"] == "CALCULADO"]
        .groupby(["sigla_uf", "ano", "mes", "nome_mes"], as_index=False)
        .agg(
            municipios=("cd_mun", "nunique"),
            precipitacao_media_mm=("precipitacao_mm", "mean"),
            normal_media_mm=("normal_mm", "mean"),
            anomalia_media_mm=("anomalia_mm", "mean"),
            anomalia_mediana_pct=("anomalia_pct", "median"),
            razao_mediana_normal=("razao_normal", "median"),
        )
    )

    anos = sorted(int(x) for x in mensal["ano"].unique())
    periodo = f"{min(anos)}_{max(anos)}"
    caminhos = {
        "mensal": pasta_saida / f"anomalias_CHIRPS_{periodo}_mensais.csv",
        "anual": pasta_saida / f"anomalias_CHIRPS_{periodo}_resumo_anual.csv",
        "uf": pasta_saida / f"anomalias_CHIRPS_{periodo}_resumo_UF_mensal.csv",
        "qualidade": pasta_saida / "relatorio_qualidade_anomalias_CHIRPS.csv",
        "parametros": pasta_saida / "parametros_execucao_anomalias.json",
    }

    mensal.to_csv(caminhos["mensal"], index=False, encoding="utf-8-sig", float_format="%.6f")
    resumo_anual.to_csv(caminhos["anual"], index=False, encoding="utf-8-sig", float_format="%.6f")
    resumo_uf.to_csv(caminhos["uf"], index=False, encoding="utf-8-sig", float_format="%.6f")

    qualidade = pd.DataFrame([
        {"indicador": "registros_mensais", "valor": len(mensal)},
        {"indicador": "municipios", "valor": mensal["cd_mun"].nunique()},
        {"indicador": "anos", "valor": len(anos)},
        {"indicador": "duplicidades", "valor": int(mensal.duplicated(["cd_mun", "ano", "mes"]).sum())},
        {"indicador": "anomalias_calculadas", "valor": int((mensal["status_calculo"] == "CALCULADO").sum())},
        {"indicador": "normais_muito_baixas", "valor": int((mensal["status_calculo"] == "NORMAL_MUITO_BAIXA").sum())},
        {"indicador": "sem_dado_observado", "valor": int((mensal["status_calculo"] == "SEM_DADO_OBSERVADO").sum())},
        {"indicador": "sem_normal_climatologica", "valor": int((mensal["status_calculo"] == "SEM_NORMAL_CLIMATOLOGICA").sum())},
    ])
    qualidade.to_csv(caminhos["qualidade"], index=False, encoding="utf-8-sig")

    metadados = {
        "data_execucao": datetime.now().isoformat(timespec="seconds"),
        "arquivo_climatologia": str(arquivo_climatologia),
        "anos_processados": anos,
        "parametros": asdict(parametros),
        "arquivos_gerados": {chave: str(valor) for chave, valor in caminhos.items() if chave != "parametros"},
    }
    caminhos["parametros"].write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "caminhos": caminhos,
        "registros": len(mensal),
        "municipios": mensal["cd_mun"].nunique(),
        "anos": anos,
        "calculados": int((mensal["status_calculo"] == "CALCULADO").sum()),
        "normais_baixas": int((mensal["status_calculo"] == "NORMAL_MUITO_BAIXA").sum()),
        "sem_dados": int((mensal["status_calculo"] == "SEM_DADO_OBSERVADO").sum()),
    }
