# Monitoramento e Cálculo de Anomalias de Precipitação CHIRPS por Município

Sistema integrado para extração de dados via **Google Earth Engine (GEE)** e processamento desktop em **Python (Tkinter/ttk)** para validação, consolidação climatológica e cálculo de anomalias de precipitação no Brasil no nível municipal.

---

## 📌 Para que serve este projeto?

O objetivo principal deste sistema é automatizar a avaliação de eventos extremos de precipitação (secas e acumulados excessivos de chuva) em todos os municípios brasileiros, utilizando a série temporal do satélite **CHIRPS v2** (*Climate Hazards Group InfraRed Precipitation with Station data*).

O sistema calcula a **Anomalia Relativa (%)** e a **Anomalia Absoluta (mm)** comparando a chuva observada no mês/ano com a **Normal Climatológica de 30 anos (1991–2020)**.

### 🌍 Onde este projeto pode ser aplicado?
* **Gestão de Recursos Hídricos & Comitês de Bacias**: Avaliação do impacto da escassez ou excesso de chuvas em reservatórios e mananciais.
* **Defesa Civil & Monitoramento de Desastres**: Identificação de municípios em situação de emergência por estiagem ou tempestades severas.
* **Agronegócio & Seguro Agrícola**: Análise de frustração de safra e risco de seca em escala municipal.
* **Pesquisa Acadêmica & Geoprocessamento**: Processamento automatizado de dados raster de sensoriamento remoto em séries tabulares prontas para análise GIS.

---

## 🏗️ Arquitetura e Fluxo de Dados

```mermaid
flowchart TD
    subgraph GEE["1. Sensoriamento Remoto (Google Earth Engine)"]
        A1["Asset IBGE 2025<br/>(BR_Municipios_2025)"] --> B1["normal_CHIRPS_1991_2020_mensal.js"]
        A1 --> B2["precipitacao_municipal_CHIRPS_anual.js"]
        CHIRPS["Série Diária CHIRPS v2<br/>(1991 - 2025)"] --> B1
        CHIRPS --> B2
        B1 -- "reduceRegions(mean)" --> C1["12 CSVs de Normal Climatológica<br/>(mes_01.csv a mes_12.csv)"]
        B2 -- "reduceRegions(mean)" --> C2["7 CSVs Observados Anuais<br/>(2019.csv a 2025.csv)"]
    end

    subgraph APP["2. Aplicação Desktop (Python / Tkinter Multithreaded)"]
        C1 --> D1["Aba 1: Validação & Consolidação Climatológica"]
        C2 --> D2["Aba 2: Validação dos Dados Observados"]
        
        D1 --> E1["Base Consolidada Longa e Larga"]
        D2 --> E2["Série Observada Validada"]
        
        P1["Aba 3: Configuração de Parâmetros"] --> F1["Aba 4: Motor de Cálculo de Anomalias"]
        E1 --> F1
        E2 --> F1
        
        F1 --> G1["Relatórios e Produtos Finais em CSV"]
    end
```

---

## 📂 Estrutura do Repositório

```text
MP1376/
├── GEE_Scripts/                              # Scripts em JavaScript para execução no Google Earth Engine
│   ├── normal_CHIRPS_1991_2020_mensal.js     # Extrai a Normal Climatológica de 30 anos (1991-2020)
│   └── precipitacao_municipal_CHIRPS_anual.js# Extrai a chuva mensal observada (2019-2025)
├── app.py                                    # Interface Gráfica Tkinter/ttk multithreaded principal
├── validacoes.py                             # Regras de validação e verificação de arquivos climatológicos
├── climatologia.py                           # Consolidação dos 12 meses da normal em tabelas longa e larga
├── observados.py                             # Validação cadastral e temporal das séries observadas
├── parametros.py                             # Modelo de dados e perfis das 7 faixas de anomalia
├── anomalias.py                              # Motor de cálculo das anomalias e enquadramento nas faixas
├── config.py                                 # Constantes globais e padrões de caminhos/arquivos
├── perfis/                                   # Perfis salvos de parâmetros (JSON)
├── assets/                                   # Diretório padrão para os arquivos CSV gerados
│   └── consolidado/                          # Produtos finais e relatórios gravados pela aplicação
├── .gitignore                                # Regras de exclusão do Git
└── README.md                                 # Documentação oficial do repositório
```

---

## ⚙️ Pré-requisitos e Instalação

### 1. Dependências do Sistema
* **Python 3.12 ou superior**
* **Google Earth Engine (Conta ativa)** para execução das extrações de sensoriamento remoto.

### 2. Instalação das Bibliotecas Python
Recomenda-se utilizar um ambiente virtual (`venv` ou `conda`):

```bash
# Clonar o repositório
git clone https://github.com/SEU_USUARIO/MP1376.git
cd MP1376

# Ativar seu ambiente virtual (exemplo conda ou venv)
# conda activate geocore

# Instalar dependências (pandas e ruff para desenvolvimento)
pip install pandas ruff
```

---

## 🚀 Guia de Uso Passo a Passo

### Passo 1: Gerar os Dados de Entrada no Google Earth Engine (GEE)

1. Abra o [Google Earth Engine Code Editor](https://code.earthengine.google.com/).
2. Certifique-se de importar o Asset municipal do IBGE ou ajuste o caminho `'projects/ee-atrigarashi/assets/IBGE/BR_Municipios_2025'` para a sua malha municipal no GEE.
3. Execute o script `GEE_Scripts/normal_CHIRPS_1991_2020_mensal.js` para gerar os 12 arquivos mensais de climatologia normal (`normal_CHIRPS_1991_2020_mes_01.csv` até `mes_12.csv`) no seu Google Drive (pasta `GEE_precipitacao`).
4. Execute o script `GEE_Scripts/precipitacao_municipal_CHIRPS_anual.js` para gerar os CSVs de precipitação observada por ano (`precipitacao_municipal_CHIRPS_2019.csv` a `2025.csv`).
5. Faça o download dos CSVs exportados e salve-os na pasta local `assets/`.

### Passo 2: Executar a Aplicação Desktop Python

Inicie a interface gráfica:

```bash
python app.py
```

A aplicação será aberta com 4 abas estruturadas:

1. **Aba 1 (Climatologia)**: Clique em *Verificar Climatologia*. Se os 12 arquivos mensais estiverem corretos, clique em *Consolidar Climatologia*.
2. **Aba 2 (Dados Observados)**: Clique em *Verificar Dados Observados* para validar os anos encontrados contra a base municipal.
3. **Aba 3 (Parâmetros)**: Inspecione ou ajuste as 7 faixas de classificação da razão $\frac{\text{Observado}}{\text{Normal}}$. Visualize o gradiente colorido no Canvas gráfico e salve/carregue perfis JSON conforme necessário.
4. **Aba 4 (Processar Anomalias)**: Clique em *Revisar Pré-requisitos* e, em seguida, em *Processar Anomalias*. O processamento será executado em segundo plano com animação contínua da barra de progresso.

---

## 📊 Faixas Padrão de Classificação de Anomalia

As anomalias são classificadas segundo a razão $R = \frac{\text{Precipitação Observada (mm)}}{\text{Normal Climatológica (mm)}}$:

| Faixa | Limites da Razão ($R$) | Anomalia Relativa (%) | Descrição |
| :--- | :---: | :---: | :--- |
| **MUITO_ABAIXO** | $R < 0,40$ | $< -60\%$ | Chuva severamente abaixo da média histórica |
| **ABAIXO** | $0,40 \le R < 0,60$ | $-60\% \text{ a } -40\%$ | Chuva moderadamente abaixo da média |
| **LIGEIRAMENTE_ABAIXO** | $0,60 \le R < 0,80$ | $-40\% \text{ a } -20\%$ | Chuva ligeiramente abaixo da média |
| **PROXIMO_DA_NORMAL** | $0,80 \le R \le 1,20$ | $-20\% \text{ a } +20\%$ | Precipitação dentro do padrão climatológico |
| **LIGEIRAMENTE_ACIMA** | $1,20 < R \le 1,40$ | $+20\% \text{ a } +40\%$ | Chuva ligeiramente acima da média |
| **ACIMA** | $1,40 < R \le 1,60$ | $+40\% \text{ a } +60\%$ | Chuva moderadamente acima da média |
| **MUITO_ACIMA** | $R > 1,60$ | $> +60\%$ | Chuva severamente acima da média histórica |

---

## 📄 Produtos e Relatórios Gerados

Ao finalizar o processamento na **Aba 4**, os produtos são gravados na pasta `assets/consolidado/`:

* `climatologia_CHIRPS_1991_2020_formato_longo.csv`: Base consolidada dos 12 meses de normal por município.
* `anomalias_CHIRPS_mensais.csv`: Tabela com precipitação observada, normal, anomalia absoluta (mm), anomalia relativa (%) e classe enquadrada.
* `relatorio_qualidade_CHIRPS.csv`: Relatório de integridade com identificação de dados nulos, negativos ou sem cobertura.

---

## 📜 Licença e Fonte dos Dados

* **Precipitação Satélite**: [CHIRPS v2](https://www.chc.ucsb.edu/data/chirps) — *Climate Hazards Center / University of California, Santa Barbara*.
* **Malha Territorial**: [IBGE](https://www.ibge.gov.br/) — *Instituto Brasileiro de Geografia e Estatística*.
