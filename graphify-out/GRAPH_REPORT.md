# Graph Report - MP1376  (2026-08-04)

## Corpus Check
- 24 files · ~16,651 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 340 nodes · 548 edges · 27 communities (18 shown, 9 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.63)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_AplicativoCHIRPS|AplicativoCHIRPS]]
- [[_COMMUNITY_.exibir_parametros|.exibir_parametros]]
- [[_COMMUNITY_app.py|app.py]]
- [[_COMMUNITY_validar_conjunto_climatologia|validar_conjunto_climatologia]]
- [[_COMMUNITY_.atualizar_texto|.atualizar_texto]]
- [[_COMMUNITY_validar_conjunto_observados|validar_conjunto_observados]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 29|Community 29]]

## God Nodes (most connected - your core abstractions)
1. `AplicativoCHIRPS` - 42 edges
2. `AplicativoCHIRPS` - 30 edges
3. `Path` - 18 edges
4. `ParametrosAnomalia` - 12 edges
5. `What You Must Do When Invoked` - 12 edges
6. `/graphify` - 11 edges
7. `Frame` - 10 edges
8. `validar_parametros()` - 10 edges
9. `parametros` - 9 edges
10. `validar_parametros()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `bool` --uses--> `ParametrosAnomalia`  [INFERRED]
  app.py → parametros.py
- `AplicativoCHIRPS` --uses--> `ParametrosAnomalia`  [INFERRED]
  app.py → parametros.py
- `Frame` --uses--> `ParametrosAnomalia`  [INFERRED]
  app.py → parametros.py
- `Text` --uses--> `ParametrosAnomalia`  [INFERRED]
  app.py → parametros.py
- `ParametrosAnomalia` --uses--> `ParametrosAnomalia`  [INFERRED]
  app.py → parametros.py

## Communities (27 total, 9 thin omitted)

### Community 0 - "AplicativoCHIRPS"
Cohesion: 0.12
Nodes (10): _classificar_razao(), processar_anomalias(), AplicativoCHIRPS, consolidar_climatologia(), Consolida os DataFrames já validados e grava os produtos em CSV., carregar_perfil(), descrever_faixas(), ParametrosAnomalia (+2 more)

### Community 1 - ".exibir_parametros"
Cohesion: 0.07
Nodes (35): Frame, AplicativoCHIRPS, Limpa todo o conteúdo de uma área de texto., Limpa todo o conteúdo de uma área de texto.          Args:             widget: W, Constrói a estrutura principal da interface gráfica., Constrói a estrutura principal da interface gráfica., Constrói a estrutura principal da interface gráfica., Cria a barra visual com o status de cada etapa do processo.          Args: (+27 more)

### Community 2 - "app.py"
Cohesion: 0.12
Nodes (22): _classificar_razao(), processar_anomalias(), Exibe a descrição textual das faixas na área de texto de parâmetros., Exibe a descrição textual das faixas na área de texto de parâmetros., Salva o perfil atual de parâmetros em um arquivo JSON., Salva o perfil atual de parâmetros em um arquivo JSON., Exibe a descrição textual das faixas na área de texto de parâmetros.          Ar, Carrega um perfil salvo de parâmetros JSON. (+14 more)

### Community 3 - "validar_conjunto_climatologia"
Cohesion: 0.33
Nodes (8): extrair_mes_do_nome(), Extrai o número do mês a partir de nomes como:      normal_CHIRPS_1991_2020_me, Abre e valida um arquivo mensal da climatologia.      Retorna um dicionário co, Verifica a presença dos 12 arquivos mensais da climatologia.      Retorna um d, Valida os nomes e o conteúdo dos 12 arquivos mensais.      Também verifica se, validar_conjunto_climatologia(), validar_conteudo_arquivo_climatologia(), verificar_arquivos_climatologia()

### Community 4 - ".atualizar_texto"
Cohesion: 0.07
Nodes (26): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+18 more)

### Community 5 - "validar_conjunto_observados"
Cohesion: 0.06
Nodes (31): bool, Atualiza o estado e a cor dos badges de etapas da interface., Atualiza o estado e a cor dos badges de etapas da interface., Atualiza o estado e a cor dos badges de etapas da interface., Inicializa a janela principal do aplicativo e suas variáveis de estado., Inicializa a janela principal do aplicativo e suas variáveis de estado., Desenha visualmente no Canvas a escala gráfica das faixas de anomalia., Desenha visualmente no Canvas a escala gráfica das faixas de anomalia. (+23 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (34): Any, Exception, Atualiza a área de texto aplicando estilos coloridos por linha., Atualiza a área de texto aplicando estilos coloridos por linha.          Args:, Executa tarefas computacionais pesadas em uma background thread desacoplada da U, Trata o retorno de sucesso na thread principal Tkinter.          Args:, Trata exceções na thread principal Tkinter.          Args:             erro: Exc, Executa o processamento final de cálculo de anomalias. (+26 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (17): anos_processados, arquivo_climatologia, arquivos_gerados, anual, mensal, qualidade, uf, data_execucao (+9 more)

### Community 8 - "Community 8"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (8): extrair_mes_do_nome(), Extrai o número do mês a partir de nomes como:      normal_CHIRPS_1991_2020_me, Abre e valida um arquivo mensal da climatologia.      Retorna um dicionário co, Verifica a presença dos 12 arquivos mensais da climatologia.      Retorna um d, Valida os nomes e o conteúdo dos 12 arquivos mensais.      Também verifica se, validar_conjunto_climatologia(), validar_conteudo_arquivo_climatologia(), verificar_arquivos_climatologia()

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (8): abaixo, acima, ligeiramente_abaixo, ligeiramente_acima, limiar_normal_mm, muito_abaixo, muito_acima, proximo_superior

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 12 - "Community 12"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 13 - "Community 13"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 14 - "Community 14"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

### Community 25 - "Community 25"
Cohesion: 1.00
Nodes (3): extrair_ano_do_nome(), validar_arquivo_observado(), validar_conjunto_observados()

### Community 29 - "Community 29"
Cohesion: 0.25
Nodes (6): Abre o seletor de diretórios para selecionar a pasta de assets., Invalida os resultados de validações prévias ao alterar diretórios., Abre o seletor de diretórios para selecionar a pasta de assets., Abre o seletor de diretórios para selecionar a pasta de assets., Invalida os resultados de validações prévias ao alterar diretórios., Invalida os resultados de validações prévias ao alterar diretórios.

## Knowledge Gaps
- **72 isolated node(s):** `PreToolUse`, `python-envs.defaultEnvManager`, `python-envs.defaultPackageManager`, `data_execucao`, `arquivo_climatologia` (+67 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AplicativoCHIRPS` connect `.exibir_parametros` to `app.py`, `Community 29`, `validar_conjunto_observados`, `Community 6`?**
  _High betweenness centrality (0.289) - this node is a cross-community bridge._
- **Why does `Path` connect `app.py` to `Community 9`, `Community 29`, `validar_conjunto_observados`, `Community 6`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `Path` (e.g. with `processar_anomalias()` and `consolidar_climatologia()`) actually correct?**
  _`Path` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `ParametrosAnomalia` (e.g. with `Any` and `bool`) actually correct?**
  _`ParametrosAnomalia` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Aplicativo desktop para validação, consolidação e cálculo de anomalias CHIRPS.`, `Inicializa a janela principal do aplicativo e suas variáveis de estado.`, `Configura a paleta de cores e os estilos dos componentes ttk.` to the rest of the system?**
  _188 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AplicativoCHIRPS` be split into smaller, more focused modules?**
  _Cohesion score 0.11738648947951273 - nodes in this community are weakly interconnected._
- **Should `.exibir_parametros` be split into smaller, more focused modules?**
  _Cohesion score 0.06767676767676768 - nodes in this community are weakly interconnected._