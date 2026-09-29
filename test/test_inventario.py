from src.elementos import Insumo
from src.inventario import Inventario


def test_hay_stock_devuelve_true_si_hay_stock_suficiente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is True

def test_hay_stock_devuelve_false_si_no_hay_stock_suficiente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 3, 0, 5)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is False

def test_hay_stock_considera_el_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 7, 5)
    requerimientos = {madera: 4}
    assert inventario.hay_stock(requerimientos) is False

def test_hay_stock_verifica_todos_los_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    clavos = Insumo("Clavos", "unidad", 3, 0, 1)
    requerimientos = {madera: 4, clavos: 5}
    assert inventario.hay_stock(requerimientos) is False

def test_reservar_aumenta_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    requerimientos = {madera: 4}
    inventario.reservar(requerimientos)
    assert madera.stock_reservado == 4
    assert madera.stock_total == 10

def test_reservar_suma_a_una_reserva_existente():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 2, 5)
    requerimientos = {madera: 4}
    inventario.reservar(requerimientos)
    assert madera.stock_reservado == 6
    assert madera.stock_total == 10

def test_reservar_varios_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 0, 5)
    clavos = Insumo("Clavos", "unidad", 20, 1, 1)
    requerimientos = {madera: 4, clavos: 5}
    inventario.reservar(requerimientos)
    assert madera.stock_reservado == 4
    assert clavos.stock_reservado == 6

def test_consumir_disminuye_stock_total_y_stock_reservado():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 4, 5)
    requerimientos = {madera: 4}
    inventario.consumir(requerimientos)
    assert madera.stock_total == 6
    assert madera.stock_reservado == 0

def test_consumir_varios_elementos():
    inventario = Inventario()
    madera = Insumo("Madera", "unidad", 10, 4, 5)
    clavos = Insumo("Clavos", "unidad", 20, 5, 1)
    requerimientos = {madera: 4, clavos: 5}
    inventario.consumir(requerimientos)
    assert madera.stock_total == 6
    assert madera.stock_reservado == 0
    assert clavos.stock_total == 15
    assert clavos.stock_reservado == 0