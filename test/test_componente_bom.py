import pytest

from src.elementos import ComponenteBOM, Insumo
from src.excepciones import CantidadInvalidaError, TipoInvalidoError


def test_crear_componente_bom():
    insumo = Insumo("Clavos", "kg", 5)
    componente = ComponenteBOM(insumo, 3)

    assert componente.elemento_produccion is insumo
    assert componente.cantidad == 3


def test_componente_bom_rechaza_elemento_invalido():
    with pytest.raises(TipoInvalidoError):
        ComponenteBOM(object(), 3)


def test_validar_cantidad_actualiza_cantidad():
    insumo = Insumo("Clavos", "kg", 5)
    componente = ComponenteBOM(insumo, 3)

    componente.validar_cantidad(5)

    assert componente.cantidad == 5


@pytest.mark.parametrize("cantidad", [0, -1, 1.5, True, "3"])
def test_validar_cantidad_rechaza_valores_invalidos(cantidad):
    insumo = Insumo("Clavos", "kg", 5)

    with pytest.raises(CantidadInvalidaError):
        ComponenteBOM(insumo, cantidad)
