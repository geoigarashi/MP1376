import re
from pathlib import Path
from typing import Any

import pandas as pd

COLUNAS_OBSERVADAS: list[str] = [
    "cd_mun",
    "nm_mun",
    "sigla_uf",
    "area_km2",
    "ano",
    "mes",
    "data",
    "precipitacao_mm",
    "fonte",
]

PADRAO_ANO = re.compile(r"_(20\d{2})\.csv$", flags=re.IGNORECASE)


def extrair_ano_do_nome(nome_arquivo: str) -> int | None:
    """Extrai o ano a partir do nome de um arquivo CSV.

    Args:
        nome_arquivo (str): Nome do arquivo a ser analisado.

    Returns:
        int | None: O ano extraído em formato numérico ou None se não encontrado.
    """
    correspondencia = PADRAO_ANO.search(nome_arquivo)
    return int(correspondencia.group(1)) if correspondencia else None


def validar_arquivo_observado(arquivo: str | Path) -> dict[str, Any]:
    """Valida a estrutura e conteúdo de um arquivo CSV de dados observados.

    Args:
        arquivo (str | Path): Caminho para o arquivo CSV a ser validado.

    Returns:
        dict[str, Any]: Dicionário contendo os indicadores de validação do arquivo.
    """
    caminho_arquivo = Path(arquivo)
    ano_esperado = extrair_ano_do_nome(caminho_arquivo.name)
    resultado: dict[str, Any] = {
        "arquivo": caminho_arquivo,
        "ano_esperado": ano_esperado,
        "leitura_ok": False,
        "erro_leitura": None,
        "colunas_ausentes": [],
        "registros": 0,
        "municipios": 0,
        "meses": [],
        "ano_compativel": False,
        "datas_incompativeis": 0,
        "codigos_invalidos": 0,
        "duplicidades": 0,
        "precipitacao_nula": 0,
        "precipitacao_negativa": 0,
        "fontes": [],
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
                "data": "string",
                "fonte": "string",
            },
            low_memory=False,
        )
    except Exception as erro:
        resultado["erro_leitura"] = str(erro)
        return resultado

    if not isinstance(base, pd.DataFrame):
        resultado["erro_leitura"] = "Leitura não retornou um DataFrame"
        return resultado

    resultado["leitura_ok"] = True
    resultado["registros"] = len(base)
    resultado["colunas_ausentes"] = [
        coluna for coluna in COLUNAS_OBSERVADAS if coluna not in base.columns
    ]
    if resultado["colunas_ausentes"]:
        return resultado

    df: pd.DataFrame = base[COLUNAS_OBSERVADAS].copy()
    df["cd_mun"] = df["cd_mun"].str.strip()
    df["nm_mun"] = df["nm_mun"].str.strip()
    df["sigla_uf"] = df["sigla_uf"].str.strip().str.upper()
    df["data"] = df["data"].str.strip()
    df["fonte"] = df["fonte"].str.strip()
    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").astype("Int64")
    df["area_km2"] = pd.to_numeric(df["area_km2"], errors="coerce")
    df["precipitacao_mm"] = pd.to_numeric(df["precipitacao_mm"], errors="coerce")

    resultado["municipios"] = int(df["cd_mun"].nunique(dropna=True))
    resultado["meses"] = sorted(int(x) for x in df["mes"].dropna().unique())
    anos = sorted(int(x) for x in df["ano"].dropna().unique())
    resultado["ano_compativel"] = ano_esperado is not None and anos == [ano_esperado]

    data_esperada = (
        df["ano"].astype("string") + "-" + df["mes"].astype("string").str.zfill(2)
    )
    resultado["datas_incompativeis"] = int((df["data"] != data_esperada).sum())
    resultado["codigos_invalidos"] = int(
        (~df["cd_mun"].str.fullmatch(r"\d{7}", na=False)).sum()
    )
    resultado["duplicidades"] = int(
        df.duplicated(subset=["cd_mun", "ano", "mes"], keep=False).sum()
    )
    resultado["precipitacao_nula"] = int(df["precipitacao_mm"].isna().sum())
    resultado["precipitacao_negativa"] = int((df["precipitacao_mm"] < 0).sum())
    resultado["fontes"] = sorted(df["fonte"].dropna().unique().tolist())

    resultado["arquivo_valido"] = (
        resultado["ano_compativel"]
        and resultado["meses"] == list(range(1, 13))
        and resultado["datas_incompativeis"] == 0
        and resultado["codigos_invalidos"] == 0
        and resultado["duplicidades"] == 0
        and resultado["precipitacao_negativa"] == 0
        and resultado["fontes"] == ["CHIRPS_v2"]
    )
    resultado["dataframe"] = df
    return resultado


def validar_conjunto_observados(
    pasta_assets: str | Path, padrao_arquivos: str, arquivo_climatologia: str | Path
) -> dict[str, Any]:
    """Valida um conjunto de arquivos observados e verifica consistência com a climatologia.

    Args:
        pasta_assets (str | Path): Diretório contendo os arquivos observados.
        padrao_arquivos (str): Padrão glob para localizar os arquivos (ex: "*.csv").
        arquivo_climatologia (str | Path): Caminho para o arquivo de climatologia de referência.

    Returns:
        dict[str, Any]: Dicionário com os resultados da validação do conjunto.
    """
    caminho_assets = Path(pasta_assets)
    caminho_climatologia = Path(arquivo_climatologia)
    arquivos = (
        sorted(caminho_assets.glob(padrao_arquivos)) if caminho_assets.is_dir() else []
    )

    resultado: dict[str, Any] = {
        "pasta_existe": caminho_assets.exists(),
        "pasta_valida": caminho_assets.is_dir(),
        "arquivo_climatologia": caminho_climatologia,
        "climatologia_existe": caminho_climatologia.exists(),
        "arquivos": [],
        "anos_encontrados": [],
        "anos_duplicados": [],
        "quantidade_validos": 0,
        "quantidade_invalidos": 0,
        "registros_totais": 0,
        "municipios_referencia": 0,
        "anos_com_municipios_diferentes": [],
        "codigos_somente_observados": [],
        "codigos_somente_climatologia": [],
        "atributos_inconsistentes": {"nm_mun": 0, "sigla_uf": 0, "area_km2": 0},
        "conjunto_valido": False,
    }
    if not resultado["pasta_valida"] or not resultado["climatologia_existe"]:
        return resultado

    por_ano: dict[int, list[Path]] = {}
    nomes_invalidos: list[str] = []
    for arq in arquivos:
        ano = extrair_ano_do_nome(arq.name)
        if ano is None:
            nomes_invalidos.append(arq.name)
        else:
            por_ano.setdefault(ano, []).append(arq)

    resultado["anos_encontrados"] = sorted(por_ano)
    resultado["anos_duplicados"] = sorted(
        ano for ano, lista in por_ano.items() if len(lista) > 1
    )

    itens: list[dict[str, Any]] = []
    for ano in resultado["anos_encontrados"]:
        for arq in por_ano[ano]:
            itens.append(validar_arquivo_observado(arq))
    resultado["arquivos"] = itens
    resultado["quantidade_validos"] = sum(item["arquivo_valido"] for item in itens)
    resultado["quantidade_invalidos"] = len(itens) - resultado["quantidade_validos"]
    resultado["registros_totais"] = sum(item["registros"] for item in itens)

    climatologia = pd.read_csv(
        caminho_climatologia,
        encoding="utf-8-sig",
        dtype={"cd_mun": "string"},
        usecols=["cd_mun", "nm_mun", "sigla_uf", "area_km2"],
        low_memory=False,
    ).drop_duplicates("cd_mun")

    if isinstance(climatologia, pd.DataFrame):
        climatologia["cd_mun"] = climatologia["cd_mun"].str.strip()
        codigos_clima = set(climatologia["cd_mun"].dropna())
    else:
        codigos_clima = set()

    resultado["municipios_referencia"] = len(codigos_clima)

    bases_validas: list[pd.DataFrame] = [
        item["dataframe"]
        for item in itens
        if isinstance(item.get("dataframe"), pd.DataFrame)
    ]
    anos_diferentes: list[int] = []
    for item in itens:
        df_item = item.get("dataframe")
        if isinstance(df_item, pd.DataFrame):
            codigos = set(df_item["cd_mun"].dropna())
            if codigos != codigos_clima:
                if item["ano_esperado"] is not None:
                    anos_diferentes.append(item["ano_esperado"])
    resultado["anos_com_municipios_diferentes"] = sorted(set(anos_diferentes))

    if bases_validas:
        unidos = pd.concat(bases_validas, ignore_index=True)
        if isinstance(unidos, pd.DataFrame):
            codigos_obs = set(unidos["cd_mun"].dropna())
            resultado["codigos_somente_observados"] = sorted(
                codigos_obs - codigos_clima
            )
            resultado["codigos_somente_climatologia"] = sorted(
                codigos_clima - codigos_obs
            )
            for coluna in ["nm_mun", "sigla_uf", "area_km2"]:
                contagens = unidos.groupby("cd_mun")[coluna].nunique(dropna=False)
                resultado["atributos_inconsistentes"][coluna] = int(
                    (contagens > 1).sum()
                )

    resultado["conjunto_valido"] = (
        bool(itens)
        and not nomes_invalidos
        and not resultado["anos_duplicados"]
        and resultado["quantidade_invalidos"] == 0
        and not resultado["anos_com_municipios_diferentes"]
        and not resultado["codigos_somente_observados"]
        and not resultado["codigos_somente_climatologia"]
        and all(v == 0 for v in resultado["atributos_inconsistentes"].values())
    )
    return resultado
