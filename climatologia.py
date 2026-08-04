from pathlib import Path

import pandas as pd

from config import (
    MESES,
    NOME_CLIMATOLOGIA_LARGA,
    NOME_CLIMATOLOGIA_LONGA,
)

NOME_SEM_DADOS = "climatologia_CHIRPS_1991_2020_sem_dados.csv"
NOME_RELATORIO_ARQUIVOS = "relatorio_arquivos_CHIRPS.csv"
NOME_RELATORIO_QUALIDADE = "relatorio_qualidade_CHIRPS.csv"


def consolidar_climatologia(resultado_validacao, pasta_saida):
    """Consolida os DataFrames já validados e grava os produtos em CSV."""
    if not resultado_validacao or not resultado_validacao.get("conjunto_valido"):
        raise ValueError(
            "O conjunto precisa ser validado com sucesso antes da consolidação."
        )

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    itens = resultado_validacao["arquivos"]
    bases = [item["dataframe"].copy() for item in itens]

    climatologia_longa = pd.concat(bases, ignore_index=True)
    climatologia_longa = climatologia_longa.sort_values(
        ["cd_mun", "mes"], kind="stable"
    ).reset_index(drop=True)

    if climatologia_longa.duplicated(["cd_mun", "mes"]).any():
        raise ValueError("A base consolidada contém duplicidades em cd_mun + mes.")

    meses_por_municipio = climatologia_longa.groupby("cd_mun")["mes"].nunique()
    if (meses_por_municipio != 12).any():
        raise ValueError("Há municípios sem os 12 registros mensais.")

    identificacao = (
        climatologia_longa[["cd_mun", "nm_mun", "sigla_uf", "area_km2"]]
        .drop_duplicates("cd_mun")
        .set_index("cd_mun")
    )

    normais_largas = climatologia_longa.pivot(
        index="cd_mun", columns="mes", values="normal_mm"
    ).rename(columns={numero: f"normal_{nome}_mm" for numero, nome in MESES.items()})

    climatologia_larga = identificacao.join(normais_largas, how="left")
    colunas_mensais = [f"normal_{nome}_mm" for nome in MESES.values()]
    climatologia_larga["normal_anual_mm"] = climatologia_larga[
        colunas_mensais
    ].sum(axis=1, min_count=12)
    climatologia_larga["meses_com_dados"] = climatologia_larga[
        colunas_mensais
    ].notna().sum(axis=1)
    climatologia_larga["status_climatologia"] = climatologia_larga[
        "meses_com_dados"
    ].eq(12).map({True: "OK", False: "INCOMPLETA"})
    climatologia_larga = climatologia_larga.reset_index().sort_values("cd_mun")

    sem_dados = climatologia_longa.loc[
        climatologia_longa["status_dados"] != "OK"
    ].copy()

    relatorio_arquivos = pd.DataFrame([
        {
            "arquivo": item["arquivo"].name,
            "mes": item["mes_esperado"],
            "registros": item["quantidade_registros"],
            "municipios": item["municipios_unicos"],
            "normal_nulos": item["normal_nulos"],
            "normal_negativos": item["normal_negativos"],
            "duplicidades": item["duplicidades"],
            "status_ok": item["status_ok"],
            "status_sem_dados": item["status_sem_dados"],
            "arquivo_valido": item["arquivo_valido"],
        }
        for item in itens
    ])

    relatorio_qualidade = pd.DataFrame([
        {"indicador": "arquivos_processados", "valor": len(itens)},
        {"indicador": "registros_consolidados", "valor": len(climatologia_longa)},
        {"indicador": "municipios_unicos", "valor": climatologia_longa["cd_mun"].nunique()},
        {"indicador": "duplicidades_cd_mun_mes", "valor": int(climatologia_longa.duplicated(["cd_mun", "mes"]).sum())},
        {"indicador": "valores_nulos_normal_mm", "valor": int(climatologia_longa["normal_mm"].isna().sum())},
        {"indicador": "registros_sem_dados", "valor": int(climatologia_longa["status_dados"].eq("SEM_DADOS").sum())},
        {"indicador": "valores_negativos", "valor": int((climatologia_longa["normal_mm"] < 0).sum())},
    ])

    caminhos = {
        "longo": pasta_saida / NOME_CLIMATOLOGIA_LONGA,
        "largo": pasta_saida / NOME_CLIMATOLOGIA_LARGA,
        "sem_dados": pasta_saida / NOME_SEM_DADOS,
        "relatorio_arquivos": pasta_saida / NOME_RELATORIO_ARQUIVOS,
        "relatorio_qualidade": pasta_saida / NOME_RELATORIO_QUALIDADE,
    }

    climatologia_longa.to_csv(caminhos["longo"], index=False, encoding="utf-8-sig", float_format="%.6f")
    climatologia_larga.to_csv(caminhos["largo"], index=False, encoding="utf-8-sig", float_format="%.6f")
    sem_dados.to_csv(caminhos["sem_dados"], index=False, encoding="utf-8-sig", float_format="%.6f")
    relatorio_arquivos.to_csv(caminhos["relatorio_arquivos"], index=False, encoding="utf-8-sig")
    relatorio_qualidade.to_csv(caminhos["relatorio_qualidade"], index=False, encoding="utf-8-sig")

    return {
        "caminhos": caminhos,
        "registros_longo": len(climatologia_longa),
        "municipios": climatologia_longa["cd_mun"].nunique(),
        "registros_sem_dados": len(sem_dados),
        "base_longa": climatologia_longa,
    }
