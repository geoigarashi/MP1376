import threading
import tkinter as tk
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from tkinter import filedialog, messagebox, ttk

from anomalias import processar_anomalias
from climatologia import consolidar_climatologia
from config import (
    NOME_CLIMATOLOGIA_LONGA,
    NOME_PASTA_CONSOLIDADO,
    PADRAO_ARQUIVOS_CLIMATOLOGIA,
    PADRAO_ARQUIVOS_OBSERVADOS,
    PASTA_ASSETS_PADRAO,
)
from observados import validar_conjunto_observados
from parametros import (
    ParametrosAnomalia,
    carregar_perfil,
    descrever_faixas,
    salvar_perfil,
    validar_parametros,
)
from validacoes import validar_conjunto_climatologia


class AplicativoCHIRPS(tk.Tk):
    """Aplicativo desktop para validação, consolidação e cálculo de anomalias CHIRPS.

    Interface gráfica desenvolvida em Tkinter/ttk com execução em background threads
    para manter a interface responsiva e a barra de progresso animada durante tarefas pesadas.
    """

    def __init__(self) -> None:
        """Inicializa a janela principal do aplicativo e suas variáveis de estado."""
        super().__init__()
        self.title("Processamento CHIRPS — Anomalias de Precipitação")
        self.geometry("980x870")
        self.minsize(860, 870)

        # Variáveis de estado
        self.pasta_assets_var = tk.StringVar(value=str(PASTA_ASSETS_PADRAO))
        self.pasta_saida_var = tk.StringVar(
            value=str(PASTA_ASSETS_PADRAO / NOME_PASTA_CONSOLIDADO)
        )
        self.status_var = tk.StringVar(value="Aplicativo pronto.")
        self.resultado_validacao_clima: Optional[Dict[str, Any]] = None
        self.resultado_validacao_observados: Optional[Dict[str, Any]] = None
        self.arquivo_climatologia_longa: Optional[Path] = None
        self.parametros_anomalia = ParametrosAnomalia()
        self.parametros_vars: Dict[str, tk.StringVar] = {}
        self._em_processamento: bool = False

        # Widgets de status e progresso
        self.badge_clima: Optional[ttk.Label] = None
        self.badge_obs: Optional[ttk.Label] = None
        self.badge_params: Optional[ttk.Label] = None
        self.progressbar: Optional[ttk.Progressbar] = None
        self.canvas_faixas: Optional[tk.Canvas] = None

        self.configurar_estilos()
        self.criar_interface()
        self.atualizar_badges()

    def configurar_estilos(self) -> None:
        """Configura a paleta de cores e os estilos dos componentes ttk."""
        self.style = ttk.Style(self)
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        # Paleta de Cores
        self.COR_BG = "#F8FAFC"
        self.COR_TEXT = "#0F172A"
        self.COR_ACCENT = "#2563EB"
        self.COR_SUCCESS = "#059669"
        self.COR_DANGER = "#DC2626"
        self.COR_WARNING = "#D97706"
        self.COR_CARD_BG = "#FFFFFF"

        self.configure(bg=self.COR_BG)

        # Estilização global
        self.style.configure(".", background=self.COR_BG, foreground=self.COR_TEXT, font=("Segoe UI", 9))
        self.style.configure("TFrame", background=self.COR_BG)
        self.style.configure("TLabelframe", background=self.COR_BG, padding=8)
        self.style.configure(
            "TLabelframe.Label",
            background=self.COR_BG,
            foreground=self.COR_ACCENT,
            font=("Segoe UI", 9, "bold"),
        )
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.COR_TEXT)
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 9), foreground="#475569")

        # Botões
        self.style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(8, 4))
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 9, "bold"),
            background=self.COR_ACCENT,
            foreground="#FFFFFF",
            padding=(10, 5),
        )
        self.style.map("Accent.TButton", background=[("active", "#1D4ED8"), ("disabled", "#94A3B8")])

        self.style.configure(
            "Success.TButton",
            font=("Segoe UI", 9, "bold"),
            background=self.COR_SUCCESS,
            foreground="#FFFFFF",
            padding=(10, 5),
        )
        self.style.map("Success.TButton", background=[("active", "#047857"), ("disabled", "#94A3B8")])

        # Badges de etapas
        self.style.configure("BadgeOK.TLabel", font=("Segoe UI", 9, "bold"), foreground=self.COR_SUCCESS)
        self.style.configure("BadgePend.TLabel", font=("Segoe UI", 9, "bold"), foreground=self.COR_WARNING)

        # Notebook (Abas)
        self.style.configure("TNotebook", background=self.COR_BG, tabmargins=[2, 4, 2, 0])
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 9, "bold"),
            padding=[12, 5],
            background="#E2E8F0",
            foreground="#334155",
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.COR_ACCENT)],
            foreground=[("selected", "#FFFFFF")],
        )

    def criar_interface(self) -> None:
        """Constrói a estrutura principal da interface gráfica."""
        principal = ttk.Frame(self, padding=(12, 8))
        principal.pack(fill="both", expand=True)

        # Cabeçalho compacto
        ttk.Label(
            principal,
            text="Processamento de Climatologia e Precipitação CHIRPS",
            style="Header.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            principal,
            text="Validação de Séries Temporais · Consolidação Climatológica · Cálculo de Anomalias",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(1, 6))

        # Painel Superior: Pastas & Badges de Progresso
        self.criar_quadro_pastas(principal)
        self.criar_painel_badges(principal)

        # Abas da Aplicação
        notebook = ttk.Notebook(principal)
        notebook.pack(fill="both", expand=True, pady=(6, 4))

        aba_clima = ttk.Frame(notebook, padding=8)
        aba_obs = ttk.Frame(notebook, padding=8)
        aba_parametros = ttk.Frame(notebook, padding=8)
        aba_processar = ttk.Frame(notebook, padding=8)

        notebook.add(aba_clima, text=" 1. Climatologia ")
        notebook.add(aba_obs, text=" 2. Dados Observados ")
        notebook.add(aba_parametros, text=" 3. Parâmetros ")
        notebook.add(aba_processar, text=" 4. Processar Anomalias ")

        self.criar_aba_climatologia(aba_clima)
        self.criar_aba_observados(aba_obs)
        self.criar_aba_parametros(aba_parametros)
        self.criar_aba_processar(aba_processar)

        # Barra de Status
        self.criar_barra_status(principal)

    def criar_painel_badges(self, pai: ttk.Frame) -> None:
        """Cria a barra visual com o status de cada etapa do processo."""
        quadro = ttk.Frame(pai)
        quadro.pack(fill="x", pady=(4, 2))

        ttk.Label(quadro, text="Status das Etapas:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))

        f1 = ttk.Frame(quadro, padding=(4, 1))
        f1.pack(side="left", padx=(0, 12))
        ttk.Label(f1, text="1. Climatologia: ").pack(side="left")
        self.badge_clima = ttk.Label(f1, text="PENDENTE 🟡", style="BadgePend.TLabel")
        self.badge_clima.pack(side="left")

        f2 = ttk.Frame(quadro, padding=(4, 1))
        f2.pack(side="left", padx=(0, 12))
        ttk.Label(f2, text="2. Observados: ").pack(side="left")
        self.badge_obs = ttk.Label(f2, text="PENDENTE 🟡", style="BadgePend.TLabel")
        self.badge_obs.pack(side="left")

        f3 = ttk.Frame(quadro, padding=(4, 1))
        f3.pack(side="left")
        ttk.Label(f3, text="3. Parâmetros: ").pack(side="left")
        self.badge_params = ttk.Label(f3, text="OK 🟢", style="BadgeOK.TLabel")
        self.badge_params.pack(side="left")

    def atualizar_badges(self) -> None:
        """Atualiza o estado e a cor dos badges de etapas da interface."""
        clima_ok = self.caminho_climatologia().exists()
        if self.badge_clima:
            self.badge_clima.configure(
                text="CONSOLIDADA 🟢" if clima_ok else "PENDENTE 🟡",
                style="BadgeOK.TLabel" if clima_ok else "BadgePend.TLabel",
            )

        obs_ok = bool(
            self.resultado_validacao_observados
            and self.resultado_validacao_observados.get("conjunto_valido")
        )
        if self.badge_obs:
            self.badge_obs.configure(
                text="VALIDADOS 🟢" if obs_ok else "PENDENTE 🟡",
                style="BadgeOK.TLabel" if obs_ok else "BadgePend.TLabel",
            )

        try:
            params = self.ler_parametros_interface()
            erros = validar_parametros(params)
        except ValueError:
            erros = ["Valores não numéricos"]
        params_ok = len(erros) == 0
        if self.badge_params:
            self.badge_params.configure(
                text="VÁLIDOS 🟢" if params_ok else "PENDENTE 🟡",
                style="BadgeOK.TLabel" if params_ok else "BadgePend.TLabel",
            )

    def criar_quadro_pastas(self, pai: ttk.Frame) -> None:
        """Cria o quadro de seleção de pastas de entrada e saída."""
        quadro = ttk.LabelFrame(pai, text="Diretórios do Processamento", padding=6)
        quadro.pack(fill="x")
        quadro.columnconfigure(1, weight=1)

        ttk.Label(quadro, text="Pasta dos assets (CSVs):").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4)
        )
        ttk.Entry(quadro, textvariable=self.pasta_assets_var).grid(
            row=0, column=1, sticky="ew", pady=(0, 4)
        )
        ttk.Button(
            quadro, text="Selecionar...", command=self.selecionar_pasta_assets
        ).grid(row=0, column=2, padx=(8, 0), pady=(0, 4))

        ttk.Label(quadro, text="Pasta de saída (Produtos):").grid(
            row=1, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Entry(quadro, textvariable=self.pasta_saida_var).grid(
            row=1, column=1, sticky="ew"
        )
        ttk.Button(
            quadro, text="Selecionar...", command=self.selecionar_pasta_saida
        ).grid(row=1, column=2, padx=(8, 0))

    def criar_area_texto(self, pai: ttk.Frame) -> tk.Text:
        """Cria uma área de texto estilizada com scrollbars."""
        quadro = ttk.LabelFrame(pai, text="Diagnóstico & Logs", padding=4)
        quadro.pack(fill="both", expand=True, pady=(6, 0))
        quadro.rowconfigure(0, weight=1)
        quadro.columnconfigure(0, weight=1)

        texto = tk.Text(
            quadro,
            wrap="none",
            height=12,
            font=("Consolas", 10),
            bg="#0F172A",
            fg="#F8FAFC",
            insertbackground="#FFFFFF",
            selectbackground="#334155",
            state="disabled",
            padx=6,
            pady=6,
        )
        texto.grid(row=0, column=0, sticky="nsew")

        texto.tag_config("sucesso", foreground="#34D399", font=("Consolas", 10, "bold"))
        texto.tag_config("erro", foreground="#F87171", font=("Consolas", 10, "bold"))
        texto.tag_config("aviso", foreground="#FBBF24", font=("Consolas", 10, "bold"))
        texto.tag_config("titulo", foreground="#60A5FA", font=("Consolas", 10, "bold"))

        scroll_y = ttk.Scrollbar(quadro, orient="vertical", command=texto.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x = ttk.Scrollbar(quadro, orient="horizontal", command=texto.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")

        texto.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        return texto

    def criar_aba_climatologia(self, aba: ttk.Frame) -> None:
        """Constrói o conteúdo da aba 1 (Climatologia)."""
        acoes = ttk.Frame(aba)
        acoes.pack(fill="x")

        ttk.Button(
            acoes,
            text="Verificar Climatologia",
            command=self.verificar_climatologia,
            style="Accent.TButton",
        ).pack(side="left")

        self.botao_consolidar = ttk.Button(
            acoes,
            text="Consolidar Climatologia",
            command=self.consolidar_climatologia_interface,
            style="Success.TButton",
            state="disabled",
        )
        self.botao_consolidar.pack(side="left", padx=(8, 0))

        ttk.Button(
            acoes, text="Limpar Log", command=lambda: self.limpar_texto(self.texto_clima)
        ).pack(side="left", padx=(8, 0))

        self.texto_clima = self.criar_area_texto(aba)

    def criar_aba_observados(self, aba: ttk.Frame) -> None:
        """Constrói o conteúdo da aba 2 (Dados Observados)."""
        ttk.Label(
            aba,
            text="Validação dos dados observados anuais em relação à climatologia consolidada.",
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w", pady=(0, 6))

        acoes = ttk.Frame(aba)
        acoes.pack(fill="x")

        self.botao_verificar_observados = ttk.Button(
            acoes,
            text="Verificar Dados Observados",
            command=self.verificar_observados,
            style="Accent.TButton",
        )
        self.botao_verificar_observados.pack(side="left")

        ttk.Button(
            acoes,
            text="Limpar Log",
            command=lambda: self.limpar_texto(self.texto_observados),
        ).pack(side="left", padx=(8, 0))

        self.texto_observados = self.criar_area_texto(aba)

    def criar_aba_parametros(self, aba: ttk.Frame) -> None:
        """Constrói o conteúdo da aba 3 (Parâmetros e Visualização de Faixas)."""
        ttk.Label(
            aba,
            text="Defina os limites para classificação da razão (Precipitação Observada / Normal Climatológica).",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 6))

        formulario = ttk.LabelFrame(aba, text="Limites de Classificação de Anomalia", padding=8)
        formulario.pack(fill="x")

        campos = [
            ("muito_abaixo", "MUITO_ABAIXO quando razão <"),
            ("abaixo", "ABAIXO até (exclusive):"),
            ("ligeiramente_abaixo", "LIGEIRAMENTE_ABAIXO até (exclusive):"),
            ("proximo_superior", "PROXIMO_DA_NORMAL até (inclusive):"),
            ("ligeiramente_acima", "LIGEIRAMENTE_ACIMA até (inclusive):"),
            ("acima", "ACIMA a partir do limite anterior e nesta faixa:"),
            ("muito_acima", "MUITO_ACIMA acima deste limite:"),
            ("limiar_normal_mm", "Normal mínima para percentual (mm):"),
        ]

        valores = vars(self.parametros_anomalia)
        for linha, (chave, rotulo) in enumerate(campos):
            col = 0 if linha < 4 else 2
            row = linha if linha < 4 else linha - 4

            ttk.Label(formulario, text=rotulo).grid(
                row=row, column=col, sticky="w", padx=(10 if col > 0 else 0, 6), pady=3
            )
            variavel = tk.StringVar(value=f"{valores[chave]:.2f}")
            self.parametros_vars[chave] = variavel
            entry = ttk.Entry(formulario, textvariable=variavel, width=12)
            entry.grid(row=row, column=col + 1, sticky="w", pady=3)
            entry.bind("<KeyRelease>", lambda e: self.desenhar_gradiente_faixas())

        quadro_canvas = ttk.LabelFrame(aba, text="Visualização Gráfica do Espectro de Faixas", padding=4)
        quadro_canvas.pack(fill="x", pady=(6, 0))

        self.canvas_faixas = tk.Canvas(quadro_canvas, height=30, bg="#0F172A", highlightthickness=0)
        self.canvas_faixas.pack(fill="x", expand=True)

        acoes = ttk.Frame(aba)
        acoes.pack(fill="x", pady=(6, 0))
        ttk.Button(
            acoes,
            text="Validar Parâmetros",
            command=self.validar_parametros_interface,
            style="Accent.TButton",
        ).pack(side="left")
        ttk.Button(
            acoes, text="Restaurar Padrão", command=self.restaurar_parametros
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            acoes, text="Salvar Perfil...", command=self.salvar_perfil_interface
        ).pack(side="left", padx=(8, 0))
        ttk.Button(
            acoes, text="Carregar Perfil...", command=self.carregar_perfil_interface
        ).pack(side="left", padx=(8, 0))

        self.texto_parametros = self.criar_area_texto(aba)
        self.exibir_parametros(self.parametros_anomalia)
        self.desenhar_gradiente_faixas()

    def desenhar_gradiente_faixas(self) -> None:
        """Desenha visualmente no Canvas a escala gráfica das faixas de anomalia."""
        if not self.canvas_faixas:
            return

        canvas = self.canvas_faixas
        canvas.delete("all")

        largura = canvas.winfo_width()
        if largura <= 1:
            largura = 800
        altura = 30

        cores = [
            ("#7F1D1D", "Muito Abaixo"),
            ("#DC2626", "Abaixo"),
            ("#F97316", "Lig. Abaixo"),
            ("#10B981", "Normal"),
            ("#3B82F6", "Lig. Acima"),
            ("#1D4ED8", "Acima"),
            ("#4C1D95", "Muito Acima"),
        ]

        num_faixas = len(cores)
        w_faixa = largura / num_faixas

        for i, (cor, label) in enumerate(cores):
            x0 = i * w_faixa
            x1 = (i + 1) * w_faixa
            canvas.create_rectangle(x0, 0, x1, altura, fill=cor, outline="#1E293B")
            canvas.create_text(
                (x0 + x1) / 2,
                altura / 2,
                text=label,
                fill="#FFFFFF",
                font=("Segoe UI", 8, "bold"),
            )

    def ler_parametros_interface(self) -> ParametrosAnomalia:
        """Lê os parâmetros numéricos dos campos de texto da interface."""
        try:
            dados = {
                chave: float(variavel.get().strip().replace(",", "."))
                for chave, variavel in self.parametros_vars.items()
            }
        except ValueError as erro:
            raise ValueError(
                "Todos os parâmetros devem ser números válidos. Use ponto ou vírgula decimal."
            ) from erro
        return ParametrosAnomalia(**dados)

    def validar_parametros_interface(self) -> bool:
        """Valida os parâmetros inseridos na interface."""
        try:
            parametros = self.ler_parametros_interface()
        except ValueError as erro:
            messagebox.showerror("Parâmetros Inválidos", str(erro))
            self.status_var.set("Há valores não numéricos nos parâmetros.")
            self.atualizar_badges()
            return False

        erros = validar_parametros(parametros)
        if erros:
            messagebox.showerror("Parâmetros Inconsistentes", "\n".join(erros))
            self.status_var.set("Os limites das faixas de anomalia são inconsistentes.")
            self.atualizar_badges()
            return False

        self.parametros_anomalia = parametros
        self.exibir_parametros(parametros)
        self.status_var.set("Parâmetros validados com sucesso.")
        self.atualizar_badges()
        self.desenhar_gradiente_faixas()
        messagebox.showinfo("Parâmetros Válidos", "As faixas de classificação estão consistentes.")
        return True

    def exibir_parametros(self, parametros: ParametrosAnomalia) -> None:
        """Exibe a descrição textual das faixas na área de texto de parâmetros."""
        linhas = [
            "PRÉVIA DAS FAIXAS DE CLASSIFICAÇÃO DE ANOMALIA",
            "=" * 78,
            "",
        ]
        linhas.extend(descrever_faixas(parametros))
        linhas.extend([
            "",
            "Conversões úteis de referência:",
            "  razão 0,50 = 50% da normal  (Anomalia: -50%)",
            "  razão 1,00 = 100% da normal (Anomalia: 0%)",
            "  razão 1,50 = 150% da normal (Anomalia: +50%)",
            "  razão 2,00 = 200% da normal (Anomalia: +100%)",
        ])
        self.atualizar_texto(self.texto_parametros, linhas)

    def restaurar_parametros(self) -> None:
        """Restaura os valores padrões de classificação de anomalia."""
        self.parametros_anomalia = ParametrosAnomalia()
        for chave, valor in vars(self.parametros_anomalia).items():
            self.parametros_vars[chave].set(f"{valor:.2f}")
        self.exibir_parametros(self.parametros_anomalia)
        self.status_var.set("Parâmetros padrão restaurados.")
        self.atualizar_badges()
        self.desenhar_gradiente_faixas()

    def salvar_perfil_interface(self) -> None:
        """Salva o perfil atual de parâmetros em um arquivo JSON."""
        try:
            parametros = self.ler_parametros_interface()
        except ValueError as erro:
            messagebox.showerror("Parâmetros Inválidos", str(erro))
            return
        erros = validar_parametros(parametros)
        if erros:
            messagebox.showerror("Parâmetros Inválidos", "\n".join(erros))
            return

        pasta_inicial = Path(__file__).resolve().parent / "perfis"
        pasta_inicial.mkdir(parents=True, exist_ok=True)
        arquivo = filedialog.asksaveasfilename(
            title="Salvar perfil de classificação",
            initialdir=str(pasta_inicial),
            initialfile="perfil_anomalias.json",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json")],
        )
        if not arquivo:
            return
        salvar_perfil(parametros, Path(arquivo))
        self.parametros_anomalia = parametros
        self.exibir_parametros(parametros)
        self.status_var.set("Perfil de parâmetros salvo com sucesso.")
        self.atualizar_badges()

    def carregar_perfil_interface(self) -> None:
        """Carrega um perfil salvo de parâmetros JSON."""
        pasta_inicial = Path(__file__).resolve().parent / "perfis"
        pasta_inicial.mkdir(parents=True, exist_ok=True)
        arquivo = filedialog.askopenfilename(
            title="Carregar perfil de classificação",
            initialdir=str(pasta_inicial),
            filetypes=[("Arquivo JSON", "*.json")],
        )
        if not arquivo:
            return
        try:
            parametros = carregar_perfil(Path(arquivo))
        except Exception as erro:
            messagebox.showerror("Erro ao Carregar Perfil", str(erro))
            return
        self.parametros_anomalia = parametros
        for chave, valor in vars(parametros).items():
            self.parametros_vars[chave].set(f"{valor:.2f}")
        self.exibir_parametros(parametros)
        self.status_var.set("Perfil de parâmetros carregado com sucesso.")
        self.atualizar_badges()
        self.desenhar_gradiente_faixas()

    def criar_aba_processar(self, aba: ttk.Frame) -> None:
        """Constrói o conteúdo da aba 4 (Processar Anomalias) com ordem corrigida dos botões."""
        ttk.Label(
            aba,
            text="Execução do cálculo de anomalias com os dados validados e parâmetros configurados.",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 6))

        acoes = ttk.Frame(aba)
        acoes.pack(fill="x")

        ttk.Button(
            acoes,
            text="Revisar Pré-requisitos",
            command=self.revisar_pre_requisitos,
            style="Accent.TButton",
        ).pack(side="left")

        self.botao_processar_anomalias = ttk.Button(
            acoes,
            text="Processar Anomalias",
            command=self.processar_anomalias_interface,
            style="Success.TButton",
        )
        self.botao_processar_anomalias.pack(side="left", padx=(8, 0))

        ttk.Button(
            acoes,
            text="Limpar Log",
            command=lambda: self.limpar_texto(self.texto_processamento),
        ).pack(side="left", padx=(8, 0))

        self.texto_processamento = self.criar_area_texto(aba)
        self.revisar_pre_requisitos()

    def _executar_em_thread(
        self, fn_tarefa: Callable[[], Any], fn_sucesso: Callable[[Any], None], fn_erro: Optional[Callable[[Exception], None]] = None
    ) -> None:
        """Executa tarefas computacionais pesadas em uma background thread desacoplada da UI.

        Args:
            fn_tarefa: Função a ser executada na thread secundária.
            fn_sucesso: Callback para a thread principal ao obter sucesso.
            fn_erro: Callback opcional para a thread principal em caso de erro.
        """
        self.iniciar_progresso()

        def worker() -> None:
            try:
                resultado = fn_tarefa()
                self.after(0, lambda res=resultado: self._ao_concluir_thread_sucesso(res, fn_sucesso))
            except Exception as err:
                self.after(0, lambda e=err: self._ao_concluir_thread_erro(e, fn_erro))

        threading.Thread(target=worker, daemon=True).start()

    def _ao_concluir_thread_sucesso(self, resultado: Any, fn_sucesso: Callable[[Any], None]) -> None:
        """Trata o retorno de sucesso na thread principal Tkinter.

        Args:
            resultado: Objeto retornado pela função de background.
            fn_sucesso: Callback de sucesso.
        """
        self.parar_progresso()
        fn_sucesso(resultado)

    def _ao_concluir_thread_erro(self, erro: Exception, fn_erro: Optional[Callable[[Exception], None]]) -> None:
        """Trata exceções na thread principal Tkinter.

        Args:
            erro: Exceção capturada na thread secundária.
            fn_erro: Callback de tratamento de erro opcional.
        """
        self.parar_progresso()
        if fn_erro:
            fn_erro(erro)
        else:
            messagebox.showerror("Erro de Execução", str(erro))

    def revisar_pre_requisitos(self) -> None:
        """Analisa os pré-requisitos necessários para execução e exibe o relatório."""
        arquivo_clima = self.caminho_climatologia()
        observados_ok = bool(
            self.resultado_validacao_observados
            and self.resultado_validacao_observados.get("conjunto_valido")
        )
        try:
            parametros = self.ler_parametros_interface()
            erros_parametros = validar_parametros(parametros)
        except ValueError as erro:
            erros_parametros = [str(erro)]

        clima_existe = arquivo_clima.exists()
        linhas = [
            "PRÉ-REQUISITOS DO PROCESSAMENTO DE ANOMALIAS",
            "=" * 84,
            f"1. Climatologia Consolidada: {'OK' if clima_existe else 'NÃO ENCONTRADA'}",
            f"   Caminho: {arquivo_clima}",
            f"2. Dados Observados Validados: {'OK' if observados_ok else 'PENDENTE'}",
            f"3. Parâmetros de Anomalia: {'OK' if not erros_parametros else 'PENDENTE'}",
            f"   Pasta de Saída: {self.pasta_saida_var.get()}",
        ]
        if erros_parametros:
            linhas.append("")
            linhas.append("Pendências nos parâmetros:")
            linhas.extend(f" - {erro}" for erro in erros_parametros)

        linhas.extend([
            "",
            "SITUAÇÃO GERAL: "
            + ("PRONTO PARA PROCESSAR OK" if (clima_existe and observados_ok and not erros_parametros) else "PENDENTE"),
        ])
        self.atualizar_texto(self.texto_processamento, linhas)
        self.atualizar_badges()

    def processar_anomalias_interface(self) -> None:
        """Executa o processamento final de cálculo de anomalias em background thread."""
        arquivo_clima = self.caminho_climatologia()
        if not arquivo_clima.exists():
            messagebox.showwarning(
                "Climatologia Não Encontrada",
                f"Consolide a climatologia primeiro.\nArquivo esperado:\n{arquivo_clima}",
            )
            return

        if not self.resultado_validacao_observados or not self.resultado_validacao_observados.get("conjunto_valido"):
            messagebox.showwarning(
                "Validação Necessária",
                "Valide os dados observados na aba 2 antes de processar.",
            )
            return

        try:
            parametros = self.ler_parametros_interface()
        except ValueError as erro:
            messagebox.showerror("Parâmetros Inválidos", str(erro))
            return
        erros = validar_parametros(parametros)
        if erros:
            messagebox.showerror("Parâmetros Inválidos", "\n".join(erros))
            return
        self.parametros_anomalia = parametros

        confirmar = messagebox.askyesno(
            "Confirmar Processamento",
            "As anomalias serão calculadas e os arquivos existentes poderão ser substituídos. Deseja continuar?",
        )
        if not confirmar:
            return

        self.status_var.set("Processando anomalias de precipitação em segundo plano...")
        self.botao_processar_anomalias.configure(state="disabled")

        pasta_saida = Path(self.pasta_saida_var.get())
        obs_dados = self.resultado_validacao_observados

        def tarefa() -> Dict[str, Any]:
            return processar_anomalias(obs_dados, arquivo_clima, pasta_saida, parametros)

        def ao_concluir(resultado: Dict[str, Any]) -> None:
            self.botao_processar_anomalias.configure(state="normal")
            periodo = f"{min(resultado['anos'])}–{max(resultado['anos'])}"
            linhas = [
                "PROCESSAMENTO DE ANOMALIAS CONCLUÍDO COM SUCESSO OK",
                "=" * 84,
                f"Período Processado: {periodo}",
                f"Registros Mensais: {resultado['registros']:,}",
                f"Municípios Cobertos: {resultado['municipios']:,}",
                f"Anomalias Relativas Calculadas: {resultado['calculados']:,}",
                f"Registros com Normal Baixa: {resultado['normais_baixas']:,}",
                f"Registros Sem Dado Observado: {resultado['sem_dados']:,}",
                "",
                "ARQUIVOS E PRODUTOS GERADOS",
                "-" * 84,
            ]
            linhas.extend(f" -> {caminho}" for caminho in resultado["caminhos"].values())
            self.atualizar_texto(self.texto_processamento, linhas)
            self.status_var.set("Anomalias processadas com sucesso.")
            messagebox.showinfo("Sucesso", "O processamento de anomalias foi concluído!")

        def ao_falhar(erro: Exception) -> None:
            self.botao_processar_anomalias.configure(state="normal")
            self.status_var.set("Erro durante o processamento das anomalias.")
            messagebox.showerror("Erro no Processamento", str(erro))

        self._executar_em_thread(tarefa, ao_concluir, ao_falhar)

    def criar_barra_status(self, pai: ttk.Frame) -> None:
        """Cria a barra inferior de status e progresso."""
        quadro = ttk.LabelFrame(pai, text="Status da Aplicação", padding=4)
        quadro.pack(fill="x", pady=(4, 0))

        ttk.Label(quadro, textvariable=self.status_var, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        self.progressbar = ttk.Progressbar(quadro, mode="indeterminate", length=160)
        self.progressbar.pack(side="right", padx=(0, 8))

        ttk.Button(quadro, text="Fechar", command=self.destroy).pack(side="right", padx=(0, 8))

    def _animar_progresso(self) -> None:
        """Anima continuamente a barra de progresso em loop."""
        if getattr(self, "_em_processamento", False) and self.progressbar:
            self.progressbar.step(8)
            self.update_idletasks()
            self.after(40, self._animar_progresso)

    def iniciar_progresso(self) -> None:
        """Inicia a animação contínua da barra de progresso."""
        self._em_processamento = True
        if self.progressbar:
            self.progressbar.configure(mode="indeterminate")
            self.progressbar.start(10)
        self._animar_progresso()

    def parar_progresso(self) -> None:
        """Para a animação da barra de progresso."""
        self._em_processamento = False
        if self.progressbar:
            self.progressbar.stop()
        self.update_idletasks()

    def selecionar_pasta_assets(self) -> None:
        """Abre o seletor de diretórios para selecionar a pasta de assets."""
        pasta = filedialog.askdirectory(
            title="Selecione a pasta contendo os arquivos CSV",
            initialdir=self.pasta_assets_var.get(),
        )
        if not pasta:
            return
        self.pasta_assets_var.set(pasta)
        self.pasta_saida_var.set(str(Path(pasta) / NOME_PASTA_CONSOLIDADO))
        self.invalidar_validacoes()
        self.status_var.set("Pasta de assets alterada. Execute as validações novamente.")

    def selecionar_pasta_saida(self) -> None:
        """Abre o seletor de diretórios para selecionar a pasta de saída."""
        inicial = Path(self.pasta_saida_var.get())
        if not inicial.exists():
            inicial = Path(self.pasta_assets_var.get())
        pasta = filedialog.askdirectory(
            title="Selecione a pasta de saída", initialdir=str(inicial)
        )
        if not pasta:
            return
        self.pasta_saida_var.set(pasta)
        self.arquivo_climatologia_longa = None
        self.resultado_validacao_observados = None
        self.status_var.set("Pasta de saída alterada.")
        self.atualizar_badges()

    def invalidar_validacoes(self) -> None:
        """Invalida os resultados de validações prévias ao alterar diretórios."""
        self.resultado_validacao_clima = None
        self.resultado_validacao_observados = None
        self.arquivo_climatologia_longa = None
        self.botao_consolidar.configure(state="disabled")
        self.atualizar_badges()

    def verificar_climatologia(self) -> None:
        """Executa a verificação dos 12 arquivos mensais de climatologia em background thread."""
        pasta_assets = Path(self.pasta_assets_var.get().strip())
        self.status_var.set("Validando os 12 arquivos da climatologia...")

        def tarefa() -> Dict[str, Any]:
            return validar_conjunto_climatologia(pasta_assets, PADRAO_ARQUIVOS_CLIMATOLOGIA)

        def ao_concluir(resultado: Dict[str, Any]) -> None:
            self.resultado_validacao_clima = resultado
            self.botao_consolidar.configure(
                state="normal" if resultado["conjunto_valido"] else "disabled"
            )
            self.exibir_climatologia(resultado)
            self.status_var.set(
                "Climatologia válida e pronta para consolidação."
                if resultado["conjunto_valido"]
                else "A climatologia possui pendências."
            )
            self.atualizar_badges()

        def ao_falhar(erro: Exception) -> None:
            messagebox.showerror("Erro de Validação", str(erro))
            self.status_var.set("Erro durante a validação da climatologia.")

        self._executar_em_thread(tarefa, ao_concluir, ao_falhar)

    def exibir_climatologia(self, resultado: Dict[str, Any]) -> None:
        """Exibe os resultados detalhados da validação de climatologia."""
        nomes = resultado["verificacao_nomes"]
        linhas = [
            "VALIDAÇÃO DA CLIMATOLOGIA",
            "=" * 78,
            f"Arquivos Localizados: {nomes['quantidade_arquivos']} de 12",
            f"Arquivos Válidos: {resultado['quantidade_validos']}",
            f"Arquivos Inválidos: {resultado['quantidade_invalidos']}",
            f"Municípios de Referência: {resultado['municipios_referencia']}",
            "",
            "Mês  Registros  Municípios  Nulos  Duplicados  Negativos  Situação",
            "-" * 78,
        ]
        for item in resultado["arquivos"]:
            linhas.append(
                f"{item['mes_esperado']:02d}   {item['quantidade_registros']:>9}  "
                f"{item['municipios_unicos']:>10}  {item['normal_nulos']:>5}  "
                f"{item['duplicidades']:>10}  {item['normal_negativos']:>9}  "
                f"{'OK' if item['arquivo_valido'] else 'ERRO'}"
            )
        linhas.extend([
            "",
            f"Conjunto Pronto para Consolidação: {'OK' if resultado['conjunto_valido'] else 'PENDENTE'}",
        ])
        self.atualizar_texto(self.texto_clima, linhas)

    def consolidar_climatologia_interface(self) -> None:
        """Interface para consolidação da climatologia em background thread."""
        if not self.resultado_validacao_clima or not self.resultado_validacao_clima.get("conjunto_valido"):
            messagebox.showwarning("Validação Necessária", "Valide a climatologia primeiro.")
            return

        self.status_var.set("Consolidando a climatologia em segundo plano...")
        pasta_saida = Path(self.pasta_saida_var.get())
        clima_validada = self.resultado_validacao_clima

        def tarefa() -> Dict[str, Any]:
            return consolidar_climatologia(clima_validada, pasta_saida)

        def ao_concluir(resultado: Dict[str, Any]) -> None:
            self.arquivo_climatologia_longa = resultado["caminhos"]["longo"]
            linhas = [
                "CONSOLIDAÇÃO DA CLIMATOLOGIA CONCLUÍDA OK",
                "=" * 78,
                f"Registros da Base Longa: {resultado['registros_longo']:,}",
                f"Municípios: {resultado['municipios']:,}",
                f"Registros SEM_DADOS: {resultado['registros_sem_dados']:,}",
                "",
                "Arquivos Gerados:",
            ]
            linhas.extend(f" -> {caminho}" for caminho in resultado["caminhos"].values())
            linhas.extend([
                "",
                "Climatologia de referência:",
                str(self.arquivo_climatologia_longa),
            ])
            self.atualizar_texto(self.texto_clima, linhas)
            self.status_var.set("Climatologia consolidada com sucesso.")
            self.atualizar_badges()
            messagebox.showinfo("Sucesso", "A climatologia foi consolidada com sucesso!")

        def ao_falhar(erro: Exception) -> None:
            messagebox.showerror("Erro na Consolidação", str(erro))
            self.status_var.set("Erro durante a consolidação.")

        self._executar_em_thread(tarefa, ao_concluir, ao_falhar)

    def caminho_climatologia(self) -> Path:
        """Retorna o caminho para o arquivo de climatologia longa consolidada."""
        if self.arquivo_climatologia_longa:
            return Path(self.arquivo_climatologia_longa)
        return Path(self.pasta_saida_var.get()) / NOME_CLIMATOLOGIA_LONGA

    def verificar_observados(self) -> None:
        """Executa a verificação das séries temporais observadas em background thread."""
        pasta_assets = Path(self.pasta_assets_var.get().strip())
        arquivo_clima = self.caminho_climatologia()
        if not arquivo_clima.exists():
            messagebox.showwarning(
                "Climatologia Não Encontrada",
                f"Consolide a climatologia antes de validar os dados observados.\n\nArquivo esperado:\n{arquivo_clima}",
            )
            return

        self.status_var.set("Validando os arquivos anuais observados em segundo plano...")

        def tarefa() -> Dict[str, Any]:
            return validar_conjunto_observados(pasta_assets, PADRAO_ARQUIVOS_OBSERVADOS, arquivo_clima)

        def ao_concluir(resultado: Dict[str, Any]) -> None:
            self.resultado_validacao_observados = resultado
            self.exibir_observados(resultado)
            self.status_var.set(
                "Dados observados válidos e prontos para o cálculo das anomalias."
                if resultado["conjunto_valido"]
                else "Os dados observados possuem pendências."
            )
            self.atualizar_badges()

        def ao_falhar(erro: Exception) -> None:
            messagebox.showerror("Erro na Validação", str(erro))
            self.status_var.set("Erro durante a validação dos dados observados.")

        self._executar_em_thread(tarefa, ao_concluir, ao_falhar)

    def exibir_observados(self, resultado: Dict[str, Any]) -> None:
        """Exibe o diagnóstico dos dados observados na área de texto."""
        anos = resultado["anos_encontrados"]
        periodo = f"{min(anos)}–{max(anos)}" if anos else "não identificado"
        linhas = [
            "VALIDAÇÃO DOS DADOS OBSERVADOS",
            "=" * 86,
            f"Climatologia Utilizada: {resultado['arquivo_climatologia']}",
            f"Período Detectado: {periodo}",
            f"Arquivos Válidos: {resultado['quantidade_validos']}",
            f"Arquivos Inválidos: {resultado['quantidade_invalidos']}",
            f"Registros Totais: {resultado['registros_totais']:,}",
            f"Municípios de Referência: {resultado['municipios_referencia']}",
            "",
            "Ano  Registros  Municípios  Meses  Nulos  Duplicados  Negativos  Situação",
            "-" * 86,
        ]
        for item in resultado["arquivos"]:
            linhas.append(
                f"{item['ano_esperado']}  {item['registros']:>9}  "
                f"{item['municipios']:>10}  {len(item['meses']):>5}  "
                f"{item['precipitacao_nula']:>5}  {item['duplicidades']:>10}  "
                f"{item['precipitacao_negativa']:>9}  "
                f"{'OK' if item['arquivo_valido'] else 'ERRO'}"
            )
        linhas.extend([
            "",
            f"Anos com conjunto municipal diferente: {resultado['anos_com_municipios_diferentes'] or 'nenhum'}",
            f"Códigos somente nos observados: {len(resultado['codigos_somente_observados'])}",
            f"Códigos somente na climatologia: {len(resultado['codigos_somente_climatologia'])}",
            f"Inconsistências em nomes: {resultado['atributos_inconsistentes']['nm_mun']}",
            f"Inconsistências em UFs: {resultado['atributos_inconsistentes']['sigla_uf']}",
            f"Inconsistências em áreas: {resultado['atributos_inconsistentes']['area_km2']}",
            "",
            f"CONJUNTO PRONTO PARA ANOMALIAS: {'OK' if resultado['conjunto_valido'] else 'PENDENTE'}",
        ])
        self.atualizar_texto(self.texto_observados, linhas)

    @staticmethod
    def atualizar_texto(widget: tk.Text, linhas: List[str]) -> None:
        """Atualiza a área de texto aplicando estilos coloridos por linha."""
        widget.configure(state="normal")
        widget.delete("1.0", "end")

        for i, linha in enumerate(linhas):
            pos_inicio = f"{i + 1}.0"
            pos_fim = f"{i + 1}.end"
            widget.insert("end", linha + "\n")

            if "=" * 10 in linha or "-" * 10 in linha or "VALIDAÇÃO" in linha or "PROCESSAMENTO" in linha:
                widget.tag_add("titulo", pos_inicio, pos_fim)
            elif " OK" in linha or " VÁLIDOS" in linha or " CONCLUÍDA" in linha or "CONCLUÍDO" in linha:
                widget.tag_add("sucesso", pos_inicio, pos_fim)
            elif "ERRO" in linha or "NÃO ENCONTRADA" in linha or "INVÁLIDO" in linha:
                widget.tag_add("erro", pos_inicio, pos_fim)
            elif "PENDENTE" in linha or "Aviso" in linha:
                widget.tag_add("aviso", pos_inicio, pos_fim)

        widget.configure(state="disabled")

    @staticmethod
    def limpar_texto(widget: tk.Text) -> None:
        """Limpa todo o conteúdo de uma área de texto."""
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.configure(state="disabled")


if __name__ == "__main__":
    AplicativoCHIRPS().mainloop()
