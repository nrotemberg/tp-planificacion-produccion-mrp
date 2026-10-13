from src.elementos import Insumo
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