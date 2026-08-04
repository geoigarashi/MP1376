"""Módulo de validação de arquivos de climatologia mensal.

Este módulo contém funções para validar nomes de arquivos, estrutura e
conteúdo dos arquivos CSV de climatologia mensal.
"""

from pathlib import Path
import re
from typing import Any

import pandas as pd

PADRAO_NUMERO_MES = re.compile(r"_mes_(\d{2})\.csv$", flags=re.IGNORECASE)

COLUNAS_CLIMATOLOGIA_OBRIGATORIAS: list[str] = [
    "cd_mun",
    "nm_mun",
    "sigla_uf",
    "area_km2",
    "mes",
    "nome_mes",
    "normal_mm",
    "status_dados",
    "ano_inicial",
    "ano_final",
    "numero_anos",
    "fonte",
    "colecao_gee",
    "periodo_referencia",
    "malha_municipal",
]

NOMES_MESES: dict[int, str] = {
    1: "jan",
    2: "fev",
    3: "mar",
    4: "abr",
    5: "mai",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "set",
    10: "out",
    11: "nov",
    12: "dez",
}


def extrair_mes_do_nome(nome_arquivo: str) -> int | None:
    """Extrai o número do mês a partir do nome do arquivo.

    Nomes esperados seguem o padrão `normal_CHIRPS_1991_2020_mes_XX.csv`.

    Args:
        nome_arquivo (str): Nome do arquivo a ser analisado.

    Returns:
        int | None: Número do mês (1 a 12) ou None se inválido.
    """
    correspondencia = PADRAO_NUMERO_MES.search(nome_arquivo)

    if correspondencia is None:
        return None

    mes = int(correspondencia.group(1))

    if mes < 1 or mes > 12:
        return None

    return mes


def verificar_arquivos_climatologia(
    pasta_assets: str | Path, padrao_arquivos: str
) -> dict[str, Any]:
    """Verifica a presença dos 12 arquivos mensais da climatologia.

    Args:
        pasta_assets (str | Path): Diretório contendo os arquivos.
        padrao_arquivos (str): Padrão glob para buscar os arquivos.

    Returns:
        dict[str, Any]: Resultados da verificação dos arquivos na pasta.
    """
    caminho_assets = Path(pasta_assets)

    resultado: dict[str, Any] = {
        "pasta_existe": caminho_assets.exists(),
        "pasta_valida": caminho_assets.is_dir(),
        "arquivos_encontrados": [],
        "quantidade_arquivos": 0,
        "meses_encontrados": [],
        "meses_ausentes": [],
        "meses_duplicados": [],
        "arquivos_nome_invalido": [],
        "pronto_para_consolidar": False,
    }

    if not caminho_assets.exists() or not caminho_assets.is_dir():
        return resultado

    arquivos = sorted(caminho_assets.glob(padrao_arquivos))

    resultado["arquivos_encontrados"] = arquivos
    resultado["quantidade_arquivos"] = len(arquivos)

    arquivos_por_mes: dict[int, list[Path]] = {}

    for arquivo in arquivos:
        mes = extrair_mes_do_nome(arquivo.name)

        if mes is None:
            resultado["arquivos_nome_invalido"].append(arquivo.name)
            continue

        arquivos_por_mes.setdefault(mes, []).append(arquivo)

    meses_encontrados = sorted(arquivos_por_mes.keys())
    meses_ausentes = [mes for mes in range(1, 13) if mes not in arquivos_por_mes]
    meses_duplicados = [
        mes for mes, lista in arquivos_por_mes.items() if len(lista) > 1
    ]

    resultado["meses_encontrados"] = meses_encontrados
    resultado["meses_ausentes"] = meses_ausentes
    resultado["meses_duplicados"] = sorted(meses_duplicados)

    resultado["pronto_para_consolidar"] = (
        len(arquivos) == 12
        and meses_encontrados == list(range(1, 13))
        and not meses_ausentes
        and not meses_duplicados
        and not resultado["arquivos_nome_invalido"]
    )

    return resultado


def validar_conteudo_arquivo_climatologia(
    arquivo: str | Path, mes_esperado: int
) -> dict[str, Any]:
    """Abre e valida um arquivo mensal da climatologia.

    Args:
        arquivo (str | Path): Caminho do arquivo a ser validado.
        mes_esperado (int): Número do mês esperado (1-12).

    Returns:
        dict[str, Any]: Resultados da validação e o DataFrame lido se válido.
    """
    caminho_arquivo = Path(arquivo)

    resultado: dict[str, Any] = {
        "arquivo": caminho_arquivo,
        "mes_esperado": mes_esperado,
        "leitura_ok": False,
        "erro_leitura": None,
        "colunas_ausentes": [],
        "quantidade_registros": 0,
        "municipios_unicos": 0,
        "meses_encontrados": [],
        "mes_compativel": False,
        "nome_mes_compativel": False,
        "codigos_invalidos": 0,
        "duplicidades": 0,
        "normal_nulos": 0,
        "normal_negativos": 0,
        "status_ok": 0,
        "status_sem_dados": 0,
        "status_outros": [],
        "ano_inicial_valores": [],
        "ano_final_valores": [],
        "numero_anos_valores": [],
        "fonte_valores": [],
        "periodo_valores": [],
        "malha_valores": [],
        "arquivo_valido": False,
        "dataframe": None,
    }

    try:
        base = pd.read_csv(
            caminho_arquivo,
            encoding="utf-8-sig",
            dtype={
                "cd_mun": "string",
                "nm_mun": "string",
                "sigla_uf": "string",
                "nome_mes": "string",
                "status_dados": "string",
                "fonte": "string",
                "colecao_gee": "string",
                "periodo_referencia": "string",
                "malha_municipal": "string",
            },
            low_memory=False,
        )
    except Exception as erro:
        resultado["erro_leitura"] = str(erro)
        return resultado

    if not isinstance(base, pd.DataFrame):
        resultado["erro_leitura"] = "O arquivo não retornou um DataFrame válido."
        return resultado

    resultado["leitura_ok"] = True
    resultado["quantidade_registros"] = len(base)

    colunas_ausentes = [
        coluna
        for coluna in COLUNAS_CLIMATOLOGIA_OBRIGATORIAS
        if coluna not in base.columns
    ]

    resultado["colunas_ausentes"] = colunas_ausentes

    if colunas_ausentes:
        return resultado

    df: pd.DataFrame = base[COLUNAS_CLIMATOLOGIA_OBRIGATORIAS].copy()

    df["cd_mun"] = df["cd_mun"].str.strip()
    df["nm_mun"] = df["nm_mun"].str.strip()
    df["sigla_uf"] = df["sigla_uf"].str.strip().str.upper()
    df["nome_mes"] = df["nome_mes"].str.strip().str.lower()
    df["status_dados"] = df["status_dados"].str.strip().str.upper()
    df["fonte"] = df["fonte"].str.strip()
    df["periodo_referencia"] = df["periodo_referencia"].str.strip()
    df["malha_municipal"] = df["malha_municipal"].str.strip()

    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")
    df["normal_mm"] = pd.to_numeric(df["normal_mm"], errors="coerce")
    df["ano_inicial"] = pd.to_numeric(df["ano_inicial"], errors="coerce").astype(
        "Int64"
    )
    df["ano_final"] = pd.to_numeric(df["ano_final"], errors="coerce").astype(
        "Int64"
    )
    df["numero_anos"] = pd.to_numeric(df["numero_anos"], errors="coerce").astype(
        "Int64"
    )

    resultado["municipios_unicos"] = df["cd_mun"].nunique(dropna=True)

    resultado["meses_encontrados"] = sorted(
        int(valor) for valor in df["mes"].dropna().unique()
    )

    resultado["mes_compativel"] = resultado["meses_encontrados"] == [mes_esperado]

    nome_mes_esperado = NOMES_MESES[mes_esperado]

    nomes_mes_encontrados = sorted(df["nome_mes"].dropna().unique().tolist())

    resultado["nome_mes_compativel"] = nomes_mes_encontrados == [
        nome_mes_esperado
    ]

    codigos_validos = df["cd_mun"].str.fullmatch(r"\d{7}", na=False)

    resultado["codigos_invalidos"] = int((~codigos_validos).sum())

    resultado["duplicidades"] = int(
        df.duplicated(subset=["cd_mun", "mes"], keep=False).sum()
    )

    resultado["normal_nulos"] = int(df["normal_mm"].isna().sum())

    resultado["normal_negativos"] = int((df["normal_mm"] < 0).sum())

    resultado["status_ok"] = int(df["status_dados"].eq("OK").sum())

    resultado["status_sem_dados"] = int(
        df["status_dados"].eq("SEM_DADOS").sum()
    )

    status_validos = {"OK", "SEM_DADOS"}

    status_encontrados = set(df["status_dados"].dropna().unique())

    resultado["status_outros"] = sorted(status_encontrados - status_validos)

    resultado["ano_inicial_valores"] = sorted(
        int(valor) for valor in df["ano_inicial"].dropna().unique()
    )

    resultado["ano_final_valores"] = sorted(
        int(valor) for valor in df["ano_final"].dropna().unique()
    )

    resultado["numero_anos_valores"] = sorted(
        int(valor) for valor in df["numero_anos"].dropna().unique()
    )

    resultado["fonte_valores"] = sorted(
        df["fonte"].dropna().unique().tolist()
    )

    resultado["periodo_valores"] = sorted(
        df["periodo_referencia"].dropna().unique().tolist()
    )

    resultado["malha_valores"] = sorted(
        df["malha_municipal"].dropna().unique().tolist()
    )

    resultado["arquivo_valido"] = (
        resultado["leitura_ok"]
        and not resultado["colunas_ausentes"]
        and resultado["quantidade_registros"] > 0
        and resultado["mes_compativel"]
        and resultado["nome_mes_compativel"]
        and resultado["codigos_invalidos"] == 0
        and resultado["duplicidades"] == 0
        and resultado["normal_negativos"] == 0
        and not resultado["status_outros"]
        and resultado["ano_inicial_valores"] == [1991]
        and resultado["ano_final_valores"] == [2020]
        and resultado["numero_anos_valores"] == [30]
        and resultado["fonte_valores"] == ["CHIRPS_v2"]
        and resultado["periodo_valores"] == ["1991-2020"]
        and resultado["malha_valores"] == ["IBGE_2024"]
    )

    resultado["dataframe"] = df

    return resultado


def validar_conjunto_climatologia(
    pasta_assets: str | Path, padrao_arquivos: str
) -> dict[str, Any]:
    """Valida os nomes e o conteúdo dos 12 arquivos mensais de climatologia.

    Args:
        pasta_assets (str | Path): Diretório contendo os arquivos.
        padrao_arquivos (str): Padrão glob para localizar os arquivos.

    Returns:
        dict[str, Any]: Dicionário com a validação consolidada do conjunto.
    """
    verificacao_nomes = verificar_arquivos_climatologia(
        pasta_assets, padrao_arquivos
    )

    resultado: dict[str, Any] = {
        "verificacao_nomes": verificacao_nomes,
        "arquivos": [],
        "quantidade_validos": 0,
        "quantidade_invalidos": 0,
        "municipios_referencia": 0,
        "meses_com_municipios_diferentes": [],
        "atributos_inconsistentes": {
            "nm_mun": 0,
            "sigla_uf": 0,
            "area_km2": 0,
        },
        "conjunto_valido": False,
    }

    if not verificacao_nomes["pronto_para_consolidar"]:
        return resultado

    arquivos_por_mes: dict[int, Path] = {}

    for arquivo in verificacao_nomes["arquivos_encontrados"]:
        mes = extrair_mes_do_nome(arquivo.name)
        if mes is not None:
            arquivos_por_mes[mes] = arquivo

    resultados_arquivos: list[dict[str, Any]] = []

    for mes in range(1, 13):
        if mes in arquivos_por_mes:
            resultado_arquivo = validar_conteudo_arquivo_climatologia(
                arquivos_por_mes[mes], mes
            )
            resultados_arquivos.append(resultado_arquivo)

    resultado["arquivos"] = resultados_arquivos

    resultado["quantidade_validos"] = sum(
        item["arquivo_valido"] for item in resultados_arquivos
    )

    resultado["quantidade_invalidos"] = (
        len(resultados_arquivos) - resultado["quantidade_validos"]
    )

    resultados_com_base = [
        item
        for item in resultados_arquivos
        if isinstance(item.get("dataframe"), pd.DataFrame)
    ]

    if not resultados_com_base:
        return resultado

    df_primeiro = resultados_com_base[0]["dataframe"]
    if isinstance(df_primeiro, pd.DataFrame):
        base_referencia = (
            df_primeiro[["cd_mun", "nm_mun", "sigla_uf", "area_km2"]]
            .drop_duplicates(subset=["cd_mun"])
            .set_index("cd_mun")
            .sort_index()
        )
        codigos_referencia = set(base_referencia.index)
    else:
        codigos_referencia = set()

    resultado["municipios_referencia"] = len(codigos_referencia)

    meses_diferentes: list[int] = []

    for item in resultados_com_base:
        base_mes = item.get("dataframe")
        if isinstance(base_mes, pd.DataFrame):
            codigos_mes = set(base_mes["cd_mun"].dropna())
            if codigos_mes != codigos_referencia:
                meses_diferentes.append(item["mes_esperado"])

    resultado["meses_com_municipios_diferentes"] = meses_diferentes

    todas_bases = pd.concat(
        [
            item["dataframe"][
                ["cd_mun", "nm_mun", "sigla_uf", "area_km2", "mes"]
            ]
            for item in resultados_com_base
            if isinstance(item.get("dataframe"), pd.DataFrame)
        ],
        ignore_index=True,
    )

    if isinstance(todas_bases, pd.DataFrame):
        for coluna in ["nm_mun", "sigla_uf", "area_km2"]:
            contagem_valores = todas_bases.groupby("cd_mun")[coluna].nunique(
                dropna=False
            )
            resultado["atributos_inconsistentes"][coluna] = int(
                (contagem_valores > 1).sum()
            )

    resultado["conjunto_valido"] = (
        resultado["quantidade_validos"] == 12
        and not resultado["meses_com_municipios_diferentes"]
        and all(
            quantidade == 0
            for quantidade in resultado["atributos_inconsistentes"].values()
        )
    )

    return resultado