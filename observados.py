import re
from pathlib import Path

import pandas as pd

COLUNAS_OBSERVADAS = [
    "cd_mun", "nm_mun", "sigla_uf", "area_km2",
    "ano", "mes", "data", "precipitacao_mm", "fonte"
]

PADRAO_ANO = re.compile(r"_(20\d{2})\.csv$", flags=re.IGNORECASE)


def extrair_ano_do_nome(nome_arquivo):
    correspondencia = PADRAO_ANO.search(nome_arquivo)
    return int(correspondencia.group(1)) if correspondencia else None


def validar_arquivo_observado(arquivo):
    arquivo = Path(arquivo)
    ano_esperado = extrair_ano_do_nome(arquivo.name)
    resultado = {
        "arquivo": arquivo,
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
            arquivo,
            encoding="utf-8-sig",
            dtype={
                "cd_mun": "string", "nm_mun": "string",
                "sigla_uf": "string", "data": "string", "fonte": "string"
            },
            low_memory=False,
        )
    except Exception as erro:
        resultado["erro_leitura"] = str(erro)
        return resultado

    resultado["leitura_ok"] = True
    resultado["registros"] = len(base)
    resultado["colunas_ausentes"] = [
        coluna for coluna in COLUNAS_OBSERVADAS if coluna not in base.columns
    ]
    if resultado["colunas_ausentes"]:
        return resultado

    base = base[COLUNAS_OBSERVADAS].copy()
    base["cd_mun"] = base["cd_mun"].str.strip()
    base["nm_mun"] = base["nm_mun"].str.strip()
    base["sigla_uf"] = base["sigla_uf"].str.strip().str.upper()
    base["data"] = base["data"].str.strip()
    base["fonte"] = base["fonte"].str.strip()
    base["ano"] = pd.to_numeric(base["ano"], errors="coerce").astype("Int64")
    base["mes"] = pd.to_numeric(base["mes"], errors="coerce").astype("Int64")
    base["area_km2"] = pd.to_numeric(base["area_km2"], errors="coerce")
    base["precipitacao_mm"] = pd.to_numeric(
        base["precipitacao_mm"], errors="coerce"
    )

    resultado["municipios"] = base["cd_mun"].nunique(dropna=True)
    resultado["meses"] = sorted(int(x) for x in base["mes"].dropna().unique())
    anos = sorted(int(x) for x in base["ano"].dropna().unique())
    resultado["ano_compativel"] = ano_esperado is not None and anos == [ano_esperado]

    data_esperada = (
        base["ano"].astype("string") + "-" + base["mes"].astype("string").str.zfill(2)
    )
    resultado["datas_incompativeis"] = int((base["data"] != data_esperada).sum())
    resultado["codigos_invalidos"] = int(
        (~base["cd_mun"].str.fullmatch(r"\d{7}", na=False)).sum()
    )
    resultado["duplicidades"] = int(
        base.duplicated(["cd_mun", "ano", "mes"], keep=False).sum()
    )
    resultado["precipitacao_nula"] = int(base["precipitacao_mm"].isna().sum())
    resultado["precipitacao_negativa"] = int((base["precipitacao_mm"] < 0).sum())
    resultado["fontes"] = sorted(base["fonte"].dropna().unique().tolist())

    resultado["arquivo_valido"] = (
        resultado["ano_compativel"]
        and resultado["meses"] == list(range(1, 13))
        and resultado["datas_incompativeis"] == 0
        and resultado["codigos_invalidos"] == 0
        and resultado["duplicidades"] == 0
        and resultado["precipitacao_negativa"] == 0
        and resultado["fontes"] == ["CHIRPS_v2"]
    )
    resultado["dataframe"] = base
    return resultado


def validar_conjunto_observados(pasta_assets, padrao_arquivos, arquivo_climatologia):
    pasta_assets = Path(pasta_assets)
    arquivo_climatologia = Path(arquivo_climatologia)
    arquivos = sorted(pasta_assets.glob(padrao_arquivos)) if pasta_assets.is_dir() else []

    resultado = {
        "pasta_existe": pasta_assets.exists(),
        "pasta_valida": pasta_assets.is_dir(),
        "arquivo_climatologia": arquivo_climatologia,
        "climatologia_existe": arquivo_climatologia.exists(),
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

    por_ano = {}
    nomes_invalidos = []
    for arquivo in arquivos:
        ano = extrair_ano_do_nome(arquivo.name)
        if ano is None:
            nomes_invalidos.append(arquivo.name)
        else:
            por_ano.setdefault(ano, []).append(arquivo)

    resultado["anos_encontrados"] = sorted(por_ano)
    resultado["anos_duplicados"] = sorted(
        ano for ano, lista in por_ano.items() if len(lista) > 1
    )

    itens = []
    for ano in resultado["anos_encontrados"]:
        for arquivo in por_ano[ano]:
            itens.append(validar_arquivo_observado(arquivo))
    resultado["arquivos"] = itens
    resultado["quantidade_validos"] = sum(item["arquivo_valido"] for item in itens)
    resultado["quantidade_invalidos"] = len(itens) - resultado["quantidade_validos"]
    resultado["registros_totais"] = sum(item["registros"] for item in itens)

    climatologia = pd.read_csv(
        arquivo_climatologia,
        encoding="utf-8-sig",
        dtype={"cd_mun": "string"},
        usecols=["cd_mun", "nm_mun", "sigla_uf", "area_km2"],
        low_memory=False,
    ).drop_duplicates("cd_mun")
    climatologia["cd_mun"] = climatologia["cd_mun"].str.strip()
    codigos_clima = set(climatologia["cd_mun"].dropna())
    resultado["municipios_referencia"] = len(codigos_clima)

    bases_validas = [item["dataframe"] for item in itens if item["dataframe"] is not None]
    anos_diferentes = []
    for item in itens:
        if item["dataframe"] is not None:
            codigos = set(item["dataframe"]["cd_mun"].dropna())
            if codigos != codigos_clima:
                anos_diferentes.append(item["ano_esperado"])
    resultado["anos_com_municipios_diferentes"] = sorted(set(anos_diferentes))

    if bases_validas:
        unidos = pd.concat(bases_validas, ignore_index=True)
        codigos_obs = set(unidos["cd_mun"].dropna())
        resultado["codigos_somente_observados"] = sorted(codigos_obs - codigos_clima)
        resultado["codigos_somente_climatologia"] = sorted(codigos_clima - codigos_obs)
        for coluna in ["nm_mun", "sigla_uf", "area_km2"]:
            contagens = unidos.groupby("cd_mun")[coluna].nunique(dropna=False)
            resultado["atributos_inconsistentes"][coluna] = int((contagens > 1).sum())

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
