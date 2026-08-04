import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class ParametrosAnomalia:
    muito_abaixo: float = 0.50
    abaixo: float = 0.75
    ligeiramente_abaixo: float = 0.90
    proximo_superior: float = 1.10
    ligeiramente_acima: float = 1.25
    acima: float = 1.50
    muito_acima: float = 2.00
    limiar_normal_mm: float = 10.0


def validar_parametros(parametros):
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

    if limites != sorted(limites) or len(set(limites)) != len(limites):
        erros.append("Os limites devem ser estritamente crescentes, sem sobreposição.")

    if parametros.limiar_normal_mm < 0:
        erros.append("A normal mínima não pode ser negativa.")

    return erros


def salvar_perfil(parametros, arquivo):
    arquivo = Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        json.dumps(asdict(parametros), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return arquivo


def carregar_perfil(arquivo):
    arquivo = Path(arquivo)
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    parametros = ParametrosAnomalia(**dados)
    erros = validar_parametros(parametros)
    if erros:
        raise ValueError("\n".join(erros))
    return parametros


def descrever_faixas(parametros):
    return [
        f"MUITO_ABAIXO: razão < {parametros.muito_abaixo:.2f}",
        (
            f"ABAIXO: {parametros.muito_abaixo:.2f} <= razão "
            f"< {parametros.abaixo:.2f}"
        ),
        (
            f"LIGEIRAMENTE_ABAIXO: {parametros.abaixo:.2f} <= razão "
            f"< {parametros.ligeiramente_abaixo:.2f}"
        ),
        (
            f"PROXIMO_DA_NORMAL: {parametros.ligeiramente_abaixo:.2f} <= razão "
            f"<= {parametros.proximo_superior:.2f}"
        ),
        (
            f"LIGEIRAMENTE_ACIMA: {parametros.proximo_superior:.2f} < razão "
            f"<= {parametros.ligeiramente_acima:.2f}"
        ),
        (
            f"ACIMA: {parametros.ligeiramente_acima:.2f} < razão "
            f"<= {parametros.acima:.2f}"
        ),
        (
            f"MUITO_ACIMA: razão > {parametros.muito_acima:.2f}"
        ),
        (
            f"Faixa entre ACIMA e MUITO_ACIMA: "
            f"{parametros.acima:.2f} < razão <= {parametros.muito_acima:.2f} "
            f"será classificada como ACIMA"
        ),
        f"Normal mínima para percentuais: {parametros.limiar_normal_mm:.2f} mm",
    ]
