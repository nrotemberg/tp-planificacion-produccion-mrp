import pytest

from src.elementos import ComponenteBOM, Insumo, Producto
from src.solicitudes import Solicitud


def crear_solicitud(cantidad=2):
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    solicitud = Solicitud(1, "Deposito", "creada", mesa, cantidad)
    return solicitud, madera, mesa


def test_crear_solicitud_y_cambiar_estado():
    solicitud, _, _ = crear_solicitud()

    assert solicitud.id == 1
    assert solicitud.solicitante == "Deposito"
    assert solicitud.estado == "creada"
    assert solicitud.cantidad == 2

    solicitud.cambiar_estado("planificada")
    assert solicitud.estado == "planificada"


def test_solicitud_rechaza_cantidad_invalida():
    producto = Producto("Mesa", "unidad", 0, 0, 1)

    with pytest.raises(ValueError):
        Solicitud(1, "Deposito", "creada", producto, 0)
