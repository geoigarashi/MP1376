import re
from pathlib import Path

import pandas as pd


PADRAO_NUMERO_MES = re.compile(
    r"_mes_(\d{2})\.csv$",
    flags=re.IGNORECASE
)


def extrair_mes_do_nome(nome_arquivo):
    """
    Extrai o número do mês a partir de nomes como:

    normal_CHIRPS_1991_2020_mes_01.csv
    normal_CHIRPS_1991_2020_mes_12.csv

    Retorna um inteiro entre 1 e 12.
    Retorna None quando o nome não segue o padrão esperado.
    """

    correspondencia = PADRAO_NUMERO_MES.search(
        nome_arquivo
    )

    if correspondencia is None:
        return None

    mes = int(correspondencia.group(1))

    if mes < 1 or mes > 12:
        return None

    return mes


def verificar_arquivos_climatologia(
    pasta_assets,
    padrao_arquivos
):
    """
    Verifica a presença dos 12 arquivos mensais da climatologia.

    Retorna um dicionário contendo:

    - situação da pasta;
    - arquivos encontrados;
    - meses encontrados;
    - meses ausentes;
    - meses duplicados;
    - arquivos cujos nomes não puderam ser interpretados.
    """

    pasta_assets = Path(pasta_assets)

    resultado = {
        "pasta_existe": pasta_assets.exists(),
        "pasta_valida": pasta_assets.is_dir(),
        "arquivos_encontrados": [],
        "quantidade_arquivos": 0,
        "meses_encontrados": [],
        "meses_ausentes": [],
        "meses_duplicados": [],
        "arquivos_nome_invalido": [],
        "pronto_para_consolidar": False
    }

    if not pasta_assets.exists():
        return resultado

    if not pasta_assets.is_dir():
        return resultado

    arquivos = sorted(
        pasta_assets.glob(padrao_arquivos)
    )

    resultado["arquivos_encontrados"] = arquivos
    resultado["quantidade_arquivos"] = len(arquivos)

    arquivos_por_mes = {}

    for arquivo in arquivos:
        mes = extrair_mes_do_nome(arquivo.name)

        if mes is None:
            resultado[
                "arquivos_nome_invalido"
            ].append(arquivo.name)

            continue

        if mes not in arquivos_por_mes:
            arquivos_por_mes[mes] = []

        arquivos_por_mes[mes].append(arquivo)

    meses_encontrados = sorted(
        arquivos_por_mes.keys()
    )

    meses_ausentes = [
        mes
        for mes in range(1, 13)
        if mes not in arquivos_por_mes
    ]

    meses_duplicados = [
        mes
        for mes, lista_arquivos
        in arquivos_por_mes.items()
        if len(lista_arquivos) > 1
    ]

    resultado["meses_encontrados"] = (
        meses_encontrados
    )

    resultado["meses_ausentes"] = meses_ausentes

    resultado["meses_duplicados"] = sorted(
        meses_duplicados
    )

    resultado["pronto_para_consolidar"] = (
        len(arquivos) == 12
        and meses_encontrados == list(range(1, 13))
        and not meses_ausentes
        and not meses_duplicados
        and not resultado["arquivos_nome_invalido"]
    )

    return resultado

COLUNAS_CLIMATOLOGIA_OBRIGATORIAS = [
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
    "malha_municipal"
]


NOMES_MESES = {
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
    12: "dez"
}


def validar_conteudo_arquivo_climatologia(
    arquivo,
    mes_esperado
):
    """
    Abre e valida um arquivo mensal da climatologia.

    Retorna um dicionário contendo os resultados da validação
    e, quando possível, o DataFrame lido.
    """

    arquivo = Path(arquivo)

    resultado = {
        "arquivo": arquivo,
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
        "dataframe": None
    }

    try:
        base = pd.read_csv(
            arquivo,
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
                "malha_municipal": "string"
            },
            low_memory=False
        )

    except Exception as erro:
        resultado["erro_leitura"] = str(erro)
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

    base = base[
        COLUNAS_CLIMATOLOGIA_OBRIGATORIAS
    ].copy()

    base["cd_mun"] = (
        base["cd_mun"]
        .str.strip()
    )

    base["nm_mun"] = (
        base["nm_mun"]
        .str.strip()
    )

    base["sigla_uf"] = (
        base["sigla_uf"]
        .str.strip()
        .str.upper()
    )

    base["nome_mes"] = (
        base["nome_mes"]
        .str.strip()
        .str.lower()
    )

    base["status_dados"] = (
        base["status_dados"]
        .str.strip()
        .str.upper()
    )

    base["fonte"] = (
        base["fonte"]
        .str.strip()
    )

    base["periodo_referencia"] = (
        base["periodo_referencia"]
        .str.strip()
    )

    base["malha_municipal"] = (
        base["malha_municipal"]
        .str.strip()
    )

    base["mes"] = pd.to_numeric(
        base["mes"],
        errors="coerce"
    ).astype("Int64")

    base["area_km2"] = pd.to_numeric(
        base["area_km2"],
        errors="coerce"
    )

    base["normal_mm"] = pd.to_numeric(
        base["normal_mm"],
        errors="coerce"
    )

    base["ano_inicial"] = pd.to_numeric(
        base["ano_inicial"],
        errors="coerce"
    ).astype("Int64")

    base["ano_final"] = pd.to_numeric(
        base["ano_final"],
        errors="coerce"
    ).astype("Int64")

    base["numero_anos"] = pd.to_numeric(
        base["numero_anos"],
        errors="coerce"
    ).astype("Int64")

    resultado["municipios_unicos"] = (
        base["cd_mun"].nunique(dropna=True)
    )

    resultado["meses_encontrados"] = sorted(
        int(valor)
        for valor in base["mes"].dropna().unique()
    )

    resultado["mes_compativel"] = (
        resultado["meses_encontrados"]
        == [mes_esperado]
    )

    nome_mes_esperado = NOMES_MESES[
        mes_esperado
    ]

    nomes_mes_encontrados = sorted(
        base["nome_mes"].dropna().unique().tolist()
    )

    resultado["nome_mes_compativel"] = (
        nomes_mes_encontrados
        == [nome_mes_esperado]
    )

    codigos_validos = (
        base["cd_mun"]
        .str.fullmatch(r"\d{7}", na=False)
    )

    resultado["codigos_invalidos"] = int(
        (~codigos_validos).sum()
    )

    resultado["duplicidades"] = int(
        base.duplicated(
            subset=["cd_mun", "mes"],
            keep=False
        ).sum()
    )

    resultado["normal_nulos"] = int(
        base["normal_mm"].isna().sum()
    )

    resultado["normal_negativos"] = int(
        (base["normal_mm"] < 0).sum()
    )

    resultado["status_ok"] = int(
        base["status_dados"].eq("OK").sum()
    )

    resultado["status_sem_dados"] = int(
        base["status_dados"]
        .eq("SEM_DADOS")
        .sum()
    )

    status_validos = {
        "OK",
        "SEM_DADOS"
    }

    status_encontrados = set(
        base["status_dados"]
        .dropna()
        .unique()
    )

    resultado["status_outros"] = sorted(
        status_encontrados - status_validos
    )

    resultado["ano_inicial_valores"] = sorted(
        int(valor)
        for valor
        in base["ano_inicial"].dropna().unique()
    )

    resultado["ano_final_valores"] = sorted(
        int(valor)
        for valor
        in base["ano_final"].dropna().unique()
    )

    resultado["numero_anos_valores"] = sorted(
        int(valor)
        for valor
        in base["numero_anos"].dropna().unique()
    )

    resultado["fonte_valores"] = sorted(
        base["fonte"]
        .dropna()
        .unique()
        .tolist()
    )

    resultado["periodo_valores"] = sorted(
        base["periodo_referencia"]
        .dropna()
        .unique()
        .tolist()
    )

    resultado["malha_valores"] = sorted(
        base["malha_municipal"]
        .dropna()
        .unique()
        .tolist()
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

    resultado["dataframe"] = base

    return resultado


def validar_conjunto_climatologia(
    pasta_assets,
    padrao_arquivos
):
    """
    Valida os nomes e o conteúdo dos 12 arquivos mensais.

    Também verifica se o conjunto de códigos municipais é o
    mesmo em todos os meses.
    """

    verificacao_nomes = verificar_arquivos_climatologia(
        pasta_assets,
        padrao_arquivos
    )

    resultado = {
        "verificacao_nomes": verificacao_nomes,
        "arquivos": [],
        "quantidade_validos": 0,
        "quantidade_invalidos": 0,
        "municipios_referencia": 0,
        "meses_com_municipios_diferentes": [],
        "atributos_inconsistentes": {
            "nm_mun": 0,
            "sigla_uf": 0,
            "area_km2": 0
        },
        "conjunto_valido": False
    }

    if not verificacao_nomes[
        "pronto_para_consolidar"
    ]:
        return resultado

    arquivos_por_mes = {}

    for arquivo in verificacao_nomes[
        "arquivos_encontrados"
    ]:
        mes = extrair_mes_do_nome(
            arquivo.name
        )

        arquivos_por_mes[mes] = arquivo

    resultados_arquivos = []

    for mes in range(1, 13):
        resultado_arquivo = (
            validar_conteudo_arquivo_climatologia(
                arquivos_por_mes[mes],
                mes
            )
        )

        resultados_arquivos.append(
            resultado_arquivo
        )

    resultado["arquivos"] = resultados_arquivos

    resultado["quantidade_validos"] = sum(
        item["arquivo_valido"]
        for item in resultados_arquivos
    )

    resultado["quantidade_invalidos"] = (
        len(resultados_arquivos)
        - resultado["quantidade_validos"]
    )

    resultados_com_base = [
        item
        for item in resultados_arquivos
        if item["dataframe"] is not None
    ]

    if not resultados_com_base:
        return resultado

    base_referencia = (
        resultados_com_base[0]["dataframe"][
            [
                "cd_mun",
                "nm_mun",
                "sigla_uf",
                "area_km2"
            ]
        ]
        .drop_duplicates(subset=["cd_mun"])
        .set_index("cd_mun")
        .sort_index()
    )

    codigos_referencia = set(
        base_referencia.index
    )

    resultado["municipios_referencia"] = len(
        codigos_referencia
    )

    meses_diferentes = []

    for item in resultados_com_base:
        base_mes = item["dataframe"]

        codigos_mes = set(
            base_mes["cd_mun"].dropna()
        )

        if codigos_mes != codigos_referencia:
            meses_diferentes.append(
                item["mes_esperado"]
            )

    resultado[
        "meses_com_municipios_diferentes"
    ] = meses_diferentes

    todas_bases = pd.concat(
        [
            item["dataframe"][
                [
                    "cd_mun",
                    "nm_mun",
                    "sigla_uf",
                    "area_km2",
                    "mes"
                ]
            ]
            for item in resultados_com_base
        ],
        ignore_index=True
    )

    for coluna in [
        "nm_mun",
        "sigla_uf",
        "area_km2"
    ]:
        contagem_valores = (
            todas_bases
            .groupby("cd_mun")[coluna]
            .nunique(dropna=False)
        )

        resultado[
            "atributos_inconsistentes"
        ][coluna] = int(
            (contagem_valores > 1).sum()
        )

    resultado["conjunto_valido"] = (
        resultado["quantidade_validos"] == 12
        and not resultado[
            "meses_com_municipios_diferentes"
        ]
        and all(
            quantidade == 0
            for quantidade
            in resultado[
                "atributos_inconsistentes"
            ].values()
        )
    )

    return resultado