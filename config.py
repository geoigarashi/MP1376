from pathlib import Path

PASTA_PROJETO_PADRAO = Path(r"C:\Python\MP1376")
PASTA_ASSETS_PADRAO = PASTA_PROJETO_PADRAO / "assets"
NOME_PASTA_CONSOLIDADO = "consolidado"

PADRAO_ARQUIVOS_CLIMATOLOGIA = "normal_CHIRPS_1991_2020_mes_*.csv"
PADRAO_ARQUIVOS_OBSERVADOS = "precipitacao_municipal_CHIRPS_*.csv"

NOME_CLIMATOLOGIA_LONGA = "climatologia_CHIRPS_1991_2020_formato_longo.csv"
NOME_CLIMATOLOGIA_LARGA = "climatologia_CHIRPS_1991_2020_formato_largo.csv"

MESES = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr",
    5: "mai", 6: "jun", 7: "jul", 8: "ago",
    9: "set", 10: "out", 11: "nov", 12: "dez"
}
