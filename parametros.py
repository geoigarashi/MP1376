import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ParametrosAnomalia:
    """Parâmetros e limites para a classificação de anomalias pluviométricas.

    Os valores padrão seguem uma escala simétrica em torno da Normal (1.00 / 100%):
    - MUITO_ABAIXO: < 0.40 (< -60%)
    - ABAIXO: 0.40 a 0.60 (-60% a -40%)
    - LIGEIRAMENTE_ABAIXO: 0.60 a 0.80 (-40% a -20%)
    - PROXIMO_DA_NORMAL: 0.80 a 1.20 (-20% a +20%)
    - LIGEIRAMENTE_ACIMA: 1.20 a 1.40 (+20% a +40%)
    - ACIMA: 1.40 a 1.60 (+40% a +60%)
    - MUITO_ACIMA: > 1.60 (> +60%)
    """

    muito_abaixo: float = 0.40
    abaixo: float = 0.60
    ligeiramente_abaixo: float = 0.80
    proximo_superior: float = 1.20
    ligeiramente_acima: float = 1.40
    acima: float = 1.60
    muito_acima: float = 1.60
    limiar_normal_mm: float = 10.0


def validar_parametros(parametros: ParametrosAnomalia) -> list[str]:
    """Valida se os limites numéricos das faixas são válidos e estritamente crescentes.

    Args:
        parametros: Instância de ParametrosAnomalia a ser validada.

    Returns:
        Lista de strings contendo as mensagens de erro encontradas (vazia se válido).
    """
    erros = []

    limites = [
        parametros.muito_abaixo,
        parametros.abaixo,
        parametros.ligeiramente_abaixo,
        parametros.proximo_superior,
        parametros.ligeiramente_acima,
        parametros.acima,
        parametros.muito_acima,
    ]

    if any(valor <= 0 for valor in limites):
        erros.append("Todos os limites de razão devem ser maiores que zero.")

    if limites != sorted(limites):
        erros.append("Os limites devem ser crescentes, sem sobreposição.")

    if (
        parametros.muito_abaixo >= parametros.abaixo
        or parametros.abaixo >= parametros.ligeiramente_abaixo
        or parametros.ligeiramente_abaixo >= parametros.proximo_superior
        or parametros.proximo_superior >= parametros.ligeiramente_acima
        or parametros.ligeiramente_acima >= parametros.acima
    ):
        erros.append("Os limites entre faixas devem ser estritamente crescentes.")

    if parametros.limiar_normal_mm < 0:
        erros.append("A normal mínima não pode ser negativa.")

    return erros


def salvar_perfil(parametros: ParametrosAnomalia, arquivo: str | Path) -> Path:
    """Salva a configuração de parâmetros de anomalia em um arquivo JSON.

    Args:
        parametros: Instância de ParametrosAnomalia com os limites configurados.
        arquivo: Caminho do arquivo JSON de destino.

    Returns:
        Objeto Path apontando para o arquivo salvo.
    """
    caminho = Path(arquivo)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(asdict(parametros), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return caminho


def carregar_perfil(arquivo: str | Path) -> ParametrosAnomalia:
    """Carrega e valida um perfil de parâmetros de anomalia a partir de um arquivo JSON.

    Args:
        arquivo: Caminho do arquivo JSON a ser lido.

    Returns:
        Instância de ParametrosAnomalia validada.

    Raises:
        ValueError: Se os parâmetros no arquivo forem inválidos.
    """
    caminho = Path(arquivo)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    parametros = ParametrosAnomalia(**dados)
    erros = validar_parametros(parametros)
    if erros:
        raise ValueError("\n".join(erros))
    return parametros


def descrever_faixas(parametros: ParametrosAnomalia) -> list[str]:
    """Gera uma lista formatada em texto descrevendo cada faixa de classificação.

    Args:
        parametros: Instância de ParametrosAnomalia.

    Returns:
        Lista de strings descrevendo cada intervalo e seu percentual.
    """
    return [
        f"MUITO_ABAIXO: razão < {parametros.muito_abaixo:.2f} (anomalia < -60%)",
        (
            f"ABAIXO: {parametros.muito_abaixo:.2f} <= razão "
            f"< {parametros.abaixo:.2f} (-60% a -40%)"
        ),
        (
            f"LIGEIRAMENTE_ABAIXO: {parametros.abaixo:.2f} <= razão "
            f"< {parametros.ligeiramente_abaixo:.2f} (-40% a -20%)"
        ),
        (
            f"PROXIMO_DA_NORMAL: {parametros.ligeiramente_abaixo:.2f} <= razão "
            f"<= {parametros.proximo_superior:.2f} (-20% a +20%)"
        ),
        (
            f"LIGEIRAMENTE_ACIMA: {parametros.proximo_superior:.2f} < razão "
            f"<= {parametros.ligeiramente_acima:.2f} (+20% a +40%)"
        ),
        (
            f"ACIMA: {parametros.ligeiramente_acima:.2f} < razão "
            f"<= {parametros.acima:.2f} (+40% a +60%)"
        ),
        (
            f"MUITO_ACIMA: razão > {parametros.acima:.2f} (anomalia > +60%)"
        ),
        f"Normal mínima para percentuais: {parametros.limiar_normal_mm:.2f} mm",
    ]
