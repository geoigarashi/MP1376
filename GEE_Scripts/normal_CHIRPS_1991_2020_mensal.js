// =====================================================================
// CLIMATOLOGIA MENSAL CHIRPS POR MUNICIPIO
// Periodo de referencia: 1991-2020
//
// Saida:
// - 12 arquivos CSV, um para cada mes
// - Media climatologica mensal em mm
// - Todos os municipios preservados
// - Campo status_dados para identificar valores ausentes
//
// Fonte:
// UCSB-CHG/CHIRPS/DAILY
// =====================================================================


// =====================================================================
// 1. PARAMETROS GERAIS
// =====================================================================

var ANO_INICIAL = 1991;
var ANO_FINAL = 2020;
var NUMERO_ANOS = ANO_FINAL - ANO_INICIAL + 1;

var ESCALA = 5566;
var TILE_SCALE = 8;
var MAX_PIXELS_REGIAO = 10000000;

var PASTA_DRIVE = 'GEE_precipitacao';

var nomesMeses = [
  'jan',
  'fev',
  'mar',
  'abr',
  'mai',
  'jun',
  'jul',
  'ago',
  'set',
  'out',
  'nov',
  'dez'
];


// =====================================================================
// 2. MALHA MUNICIPAL
//
// ALTERE SOMENTE O CAMINHO ABAIXO PARA O ID DO SEU ASSET.
// =====================================================================

var municipios = ee.FeatureCollection(
  'projects/ee-atrigarashi/assets/IBGE/BR_Municipios_2025'
);

// Manter somente os campos necessários.
//
// Caso os nomes dos campos no seu asset sejam diferentes,
// faça o ajuste aqui.
municipios = municipios.select([
  'CD_MUN',
  'NM_MUN',
  'SIGLA_UF',
  'AREA_KM2'
]);


// =====================================================================
// 3. COLECAO DIARIA CHIRPS
// =====================================================================

// A data final do filterDate e exclusiva.
// Assim, 2021-01-01 encerra corretamente o período em 2020-12-31.

var DATA_INICIAL = ee.Date.fromYMD(ANO_INICIAL, 1, 1);
var DATA_FINAL = ee.Date.fromYMD(ANO_FINAL + 1, 1, 1);

var chirps = ee.ImageCollection(
  'UCSB-CHG/CHIRPS/DAILY'
)
  .filterDate(DATA_INICIAL, DATA_FINAL)
  .select('precipitation');


// =====================================================================
// 4. VERIFICACOES LEVES
//
// Estas chamadas não executam a redução nacional.
// =====================================================================

print(
  'Período da climatologia:',
  ANO_INICIAL + '-' + ANO_FINAL
);

print(
  'Número de anos:',
  NUMERO_ANOS
);

print(
  'Número de imagens diárias CHIRPS:',
  chirps.size()
);

print(
  'Quantidade de municípios:',
  municipios.size()
);

print(
  'Primeiro município:',
  municipios.first()
);


// =====================================================================
// 5. FUNCAO PARA GERAR A NORMAL DE UM MES
//
// Para cada mês:
//
// 1. seleciona todos os dias daquele mês entre 1991 e 2020;
// 2. soma a precipitação de todos os dias;
// 3. divide o resultado por 30 anos.
//
// Exemplo para janeiro:
//
// soma de todos os dias de janeiro de 1991 a 2020 / 30
//
// Isso equivale à média dos 30 totais mensais de janeiro.
// =====================================================================

function gerarNormalMensal(numeroMes) {

  numeroMes = ee.Number(numeroMes);

  var diasDoMes = chirps.filter(
    ee.Filter.calendarRange(
      numeroMes,
      numeroMes,
      'month'
    )
  );

  var normalMensal = diasDoMes
    .sum()
    .divide(NUMERO_ANOS)
    .rename('normal_mm');

  return normalMensal.set({
    mes: numeroMes,
    ano_inicial: ANO_INICIAL,
    ano_final: ANO_FINAL,
    numero_anos: NUMERO_ANOS,
    fonte: 'CHIRPS_v2',
    periodo_referencia: '1991-2020'
  });
}


// =====================================================================
// 6. FUNCAO PARA CALCULAR A NORMAL POR MUNICIPIO
//
// Importante:
//
// - não calcula o coeficiente de variação;
// - não converte valores nulos com ee.Number();
// - não executa gt(), divide() ou multiply() em valores nulos;
// - municípios sem pixels válidos são preservados;
// - status_dados recebe "OK" ou "SEM_DADOS".
// =====================================================================

function calcularMunicipiosPorMes(numeroMes) {

  var imagemNormal = gerarNormalMensal(numeroMes);

  var resultados = imagemNormal.reduceRegions({
    collection: municipios,
    reducer: ee.Reducer.mean(),
    scale: ESCALA,
    tileScale: TILE_SCALE,
    maxPixelsPerRegion: MAX_PIXELS_REGIAO
  });

  resultados = resultados.map(function(feature) {

    // A saída do Reducer.mean() chama-se "mean".
    //
    // Não usamos ee.Number() aqui porque a propriedade poderá
    // ser nula para alguma geometria sem cobertura válida.

    var normalRaw = feature.get('mean');

    var statusDados = ee.Algorithms.If(
      ee.Algorithms.IsEqual(normalRaw, null),
      'SEM_DADOS',
      'OK'
    );

    return ee.Feature(null, {
      cd_mun: feature.get('CD_MUN'),
      nm_mun: feature.get('NM_MUN'),
      sigla_uf: feature.get('SIGLA_UF'),
      area_km2: feature.get('AREA_KM2'),

      mes: numeroMes,
      nome_mes: nomesMeses[numeroMes - 1],

      normal_mm: normalRaw,
      status_dados: statusDados,

      ano_inicial: ANO_INICIAL,
      ano_final: ANO_FINAL,
      numero_anos: NUMERO_ANOS,

      fonte: 'CHIRPS_v2',
      colecao_gee: 'UCSB-CHG/CHIRPS/DAILY',
      periodo_referencia: '1991-2020',
      malha_municipal: 'IBGE_2024'
    });
  });

  return resultados;
}


// =====================================================================
// 7. TESTE CONTROLADO
//
// O teste usa somente janeiro e os primeiros 10 municípios.
// Não tente imprimir o resultado nacional completo no console.
// =====================================================================

var municipiosTeste = municipios.limit(10);

var imagemJaneiroTeste = gerarNormalMensal(1);

var resultadoTeste = imagemJaneiroTeste.reduceRegions({
  collection: municipiosTeste,
  reducer: ee.Reducer.mean(),
  scale: ESCALA,
  tileScale: 4,
  maxPixelsPerRegion: MAX_PIXELS_REGIAO
});

resultadoTeste = resultadoTeste.map(function(feature) {

  var normalRaw = feature.get('mean');

  var statusDados = ee.Algorithms.If(
    ee.Algorithms.IsEqual(normalRaw, null),
    'SEM_DADOS',
    'OK'
  );

  return ee.Feature(null, {
    cd_mun: feature.get('CD_MUN'),
    nm_mun: feature.get('NM_MUN'),
    sigla_uf: feature.get('SIGLA_UF'),
    mes: 1,
    nome_mes: 'jan',
    normal_mm: normalRaw,
    status_dados: statusDados
  });
});

print(
  'Teste de janeiro para 10 municípios:',
  resultadoTeste
);


// =====================================================================
// 8. COLUNAS DOS ARQUIVOS CSV
// =====================================================================

var colunasExportacao = [
  'cd_mun',
  'nm_mun',
  'sigla_uf',
  'area_km2',

  'mes',
  'nome_mes',

  'normal_mm',
  'status_dados',

  'ano_inicial',
  'ano_final',
  'numero_anos',

  'fonte',
  'colecao_gee',
  'periodo_referencia',
  'malha_municipal'
];


// =====================================================================
// 9. EXPORTACOES
//
// O script cria 12 tarefas, uma para cada mês.
//
// Os arquivos serão:
//
// normal_CHIRPS_1991_2020_mes_01.csv
// normal_CHIRPS_1991_2020_mes_02.csv
// ...
// normal_CHIRPS_1991_2020_mes_12.csv
// =====================================================================

for (var mes = 1; mes <= 12; mes++) {

  var numeroMesTexto = ('0' + mes).slice(-2);

  var resultadoMes = calcularMunicipiosPorMes(mes);

  Export.table.toDrive({
    collection: resultadoMes,

    description:
      'normal_CHIRPS_1991_2020_mes_' +
      numeroMesTexto,

    folder:
      PASTA_DRIVE,

    fileNamePrefix:
      'normal_CHIRPS_1991_2020_mes_' +
      numeroMesTexto,

    fileFormat:
      'CSV',

    selectors:
      colunasExportacao
  });
}
