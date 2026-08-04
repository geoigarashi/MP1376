// ============================================================
// PRECIPITACAO MENSAL POR MUNICIPIO - CHIRPS
// Periodo: janeiro/2019 a dezembro/2025
// ============================================================

// 1. Malha municipal importada como asset
var municipios = ee.FeatureCollection(
  'projects/ee-atrigarashi/assets/IBGE/BR_Municipios_2025'
);

// Manter somente os campos necessários.
// Ajuste os nomes se forem diferentes no seu shapefile.
municipios = municipios.select([
  'CD_MUN',
  'NM_MUN',
  'SIGLA_UF',
  'AREA_KM2'
]);

// 2. Coleção diária CHIRPS
var chirps = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY')
  .select('precipitation')
  .filterDate('2019-01-01', '2026-01-01');

// 3. Função que calcula um mês
function calcularMes(ano, mes) {
  ano = ee.Number(ano);
  mes = ee.Number(mes);

  var inicio = ee.Date.fromYMD(ano, mes, 1);
  var fim = inicio.advance(1, 'month');

  // Soma dos valores diários = total mensal em mm
  var precipitacaoMensal = chirps
    .filterDate(inicio, fim)
    .sum()
    .rename('precipitacao_mm');

  // Média espacial dos pixels dentro de cada município
  var resultado = precipitacaoMensal.reduceRegions({
    collection: municipios,
    reducer: ee.Reducer.mean(),
    scale: 5566,
    crs: 'EPSG:4326',
    tileScale: 4
  });

  // Acrescenta informações temporais e remove geometria
  resultado = resultado.map(function(feature) {
    return ee.Feature(null, {
      cd_mun: feature.get('CD_MUN'),
      nm_mun: feature.get('NM_MUN'),
      sigla_uf: feature.get('SIGLA_UF'),
      area_km2: feature.get('AREA_KM2'),
      ano: ano,
      mes: mes,
      data: inicio.format('YYYY-MM'),
      precipitacao_mm: feature.get('mean'),
      fonte: 'CHIRPS_v2'
    });
  });

  return resultado;
}

// 4. Função que gera os 12 meses de um determinado ano
function calcularAno(ano) {
  var meses = ee.List.sequence(1, 12);

  var colecoesMensais = meses.map(function(mes) {
    return calcularMes(ano, mes);
  });

  return ee.FeatureCollection(colecoesMensais).flatten();
}

// 5. Visualização de teste: janeiro de 2019
var teste = calcularMes(2019, 1);

print('Amostra janeiro de 2019:', teste.limit(10));
print('Quantidade esperada no mês:', teste.size());

// Map.centerObject(municipios, 4);
Map.addLayer(
  municipios.style({
    color: '555555',
    fillColor: '00000000',
    width: 1
  }),
  {},
  'Municipios'
);

// ============================================================
// 6. EXPORTACOES - UMA POR ANO
// ============================================================

var resultado2019 = calcularAno(2019);
var resultado2020 = calcularAno(2020);
var resultado2021 = calcularAno(2021);
var resultado2022 = calcularAno(2022);
var resultado2023 = calcularAno(2023);
var resultado2024 = calcularAno(2024);
var resultado2025 = calcularAno(2025);

var colunas = [
  'cd_mun',
  'nm_mun',
  'sigla_uf',
  'area_km2',
  'ano',
  'mes',
  'data',
  'precipitacao_mm',
  'fonte'
];

Export.table.toDrive({
  collection: resultado2019,
  description: 'precipitacao_municipal_CHIRPS_2019',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2019',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2020,
  description: 'precipitacao_municipal_CHIRPS_2020',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2020',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2021,
  description: 'precipitacao_municipal_CHIRPS_2021',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2021',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2022,
  description: 'precipitacao_municipal_CHIRPS_2022',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2022',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2023,
  description: 'precipitacao_municipal_CHIRPS_2023',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2023',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2024,
  description: 'precipitacao_municipal_CHIRPS_2024',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2024',
  fileFormat: 'CSV',
  selectors: colunas
});

Export.table.toDrive({
  collection: resultado2025,
  description: 'precipitacao_municipal_CHIRPS_2025',
  folder: 'GEE_precipitacao',
  fileNamePrefix: 'precipitacao_municipal_CHIRPS_2025',
  fileFormat: 'CSV',
  selectors: colunas
});