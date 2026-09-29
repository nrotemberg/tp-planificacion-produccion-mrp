import pytest
from src.elementos import ComponenteBOM, Insumo, Producto
from src.excepciones import CantidadInvalidaError
from src.solicitudes import Solicitud


def crear_solicitud(cantidad=2):
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    solicitud = Solicitud(1, "Deposito", mesa, cantidad)
    return solicitud, madera, mesa

def test_crear_solicitud_y_cambiar_estado():
    solicitud, _, _ = crear_solicitud()
    assert solicitud.id == 1
    assert solicitud.solicitante == "Deposito"
    assert solicitud.estado == "creada"
    assert solicitud.cantidad == 2
    assert solicitud.producto.nombre == "Mesa"

    resultado = solicitud.cambiar_estado()
    assert resultado is True
    assert solicitud.estado == "planificada"

def test_solicitud_avanza_por_todos_los_estados():
    solicitud, _, _ = crear_solicitud()
    assert solicitud.estado == "creada"
    assert solicitud.cambiar_estado() is True
    assert solicitud.estado == "planificada"
    assert solicitud.cambiar_estado() is True
    assert solicitud.estado == "en curso"
    assert solicitud.cambiar_estado() is True
    assert solicitud.estado == "finalizada"

def test_solicitud_finalizada_no_puede_avanzar_mas():
    solicitud, _, _ = crear_solicitud()
    solicitud.cambiar_estado()
    solicitud.cambiar_estado()
    solicitud.cambiar_estado()
    resultado = solicitud.cambiar_estado()
    assert resultado is False
    assert solicitud.estado == "finalizada"


@pytest.mark.parametrize("cantidad", [0, -1, 1.5, "2", None, True])
def test_solicitud_rechaza_cantidad_invalida(cantidad):
    producto = Producto("Mesa", "unidad", 0, 0, 1)
    with pytest.raises(CantidadInvalidaError):
        Solicitud(1, "Deposito", producto, cantidad)
