import pytest

from src.elementos import Insumo


def test_get_costo():
    insumo = Insumo("Harina", "kg", 50, 0, 20)

    assert insumo.get_costo() == 20


def test_actualizar_costo():
    insumo = Insumo("Harina", "kg", 50, 0, 20)

    insumo.actualizar_costo(25)

    assert insumo.get_costo() == 25


def test_actualizar_costo_rechaza_valor_invalido():
    insumo = Insumo("Harina", "kg", 50, 0, 20)

    with pytest.raises(ValueError):
        insumo.actualizar_costo(0)
