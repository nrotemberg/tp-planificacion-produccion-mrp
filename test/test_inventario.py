import pytest

from src.elementos import Insumo
from src.excepciones import CantidadInvalidaError, StockInsuficienteError
from src.inventario import Inventario


def test_hay_stock_devuelve_true_si_hay_stock_suficiente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is True

def test_hay_stock_devuelve_false_si_no_hay_stock_suficiente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 3)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is False

def test_hay_stock_considera_el_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10, 7)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is False

def test_hay_stock_verifica_todos_los_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    inventario.registrar(madera, 10)
    inventario.registrar(clavos, 3)
    requerimientos = {madera: 4, clavos: 5}
    assert inventario.hay_stock(requerimientos) is False

def test_reservar_aumenta_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10)
    requerimientos = {madera: 4}
    inventario.reservar(requerimientos)
    assert inventario.stock[madera]["reservado"] == 4
    assert inventario.stock[madera]["actual"] == 10

def test_reservar_suma_a_una_reserva_existente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10, 2)
    requerimientos = {madera: 4}
    inventario.reservar(requerimientos)
    assert inventario.stock[madera]["reservado"] == 6
    assert inventario.stock[madera]["actual"] == 10

def test_reservar_varios_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    inventario.registrar(madera, 10)
    inventario.registrar(clavos, 20, 1)
    requerimientos = {madera: 4, clavos: 5}
    inventario.reservar(requerimientos)
    assert inventario.stock[madera]["reservado"] == 4
    assert inventario.stock[clavos]["reservado"] == 6

def test_consumir_disminuye_stock_total_y_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10, 4)
    requerimientos = {madera: 4}
    inventario.consumir(requerimientos)
    assert inventario.stock[madera]["actual"] == 6
    assert inventario.stock[madera]["reservado"] == 0

def test_consumir_varios_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    inventario.registrar(madera, 10, 4)
    inventario.registrar(clavos, 20, 5)
    requerimientos = {madera: 4, clavos: 5}
    inventario.consumir(requerimientos)
    assert inventario.stock[madera]["actual"] == 6
    assert inventario.stock[madera]["reservado"] == 0
    assert inventario.stock[clavos]["actual"] == 15
    assert inventario.stock[clavos]["reservado"] == 0


@pytest.mark.parametrize(
    "stock_actual, stock_reservado",
    [
        (-1, 0),
        (1, -1),
        (1, 2),
        (True, 0),
        (1, 0.5),
    ],
)
def test_registrar_rechaza_stock_invalido(stock_actual, stock_reservado):
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)

    with pytest.raises(CantidadInvalidaError):
        inventario.registrar(madera, stock_actual, stock_reservado)

    assert madera not in inventario.stock


@pytest.mark.parametrize("cantidad", [0, -1, True, 1.5])
def test_agregar_stock_rechaza_cantidades_invalidas(cantidad):
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10)

    with pytest.raises(CantidadInvalidaError):
        inventario.agregar_stock(madera, cantidad)

    assert inventario.obtener_stock(madera) == {
        "actual": 10,
        "reservado": 0,
    }


@pytest.mark.parametrize("cantidad", [0, -1, True, 1.5])
def test_hay_stock_rechaza_requerimientos_invalidos(cantidad):
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    inventario.registrar(madera, 10)

    with pytest.raises(CantidadInvalidaError):
        inventario.hay_stock({madera: cantidad})


def test_reservar_rechaza_stock_insuficiente_sin_cambios_parciales():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    inventario.registrar(madera, 10)
    inventario.registrar(clavos, 2)

    with pytest.raises(StockInsuficienteError):
        inventario.reservar({madera: 4, clavos: 3})

    assert inventario.obtener_stock(madera) == {
        "actual": 10,
        "reservado": 0,
    }
    assert inventario.obtener_stock(clavos) == {
        "actual": 2,
        "reservado": 0,
    }


def test_consumir_rechaza_stock_no_reservado_sin_cambios_parciales():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    inventario.registrar(madera, 10, 4)
    inventario.registrar(clavos, 20, 2)

    with pytest.raises(StockInsuficienteError):
        inventario.consumir({madera: 4, clavos: 3})

    assert inventario.obtener_stock(madera) == {
        "actual": 10,
        "reservado": 4,
    }
    assert inventario.obtener_stock(clavos) == {
        "actual": 20,
        "reservado": 2,
    }