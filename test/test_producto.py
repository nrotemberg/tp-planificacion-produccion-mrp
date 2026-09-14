import pytest

from src.elementos import ComponenteBOM, Insumo, Producto


def test_costo_unitario_con_insumos():
    madera = Insumo("Madera", "unidad", 20, 0, 10)
    clavos = Insumo("Clavos", "unidad", 20, 0, 2)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)

    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(clavos, 4))

    assert mesa.costo_unitario() == 28
    assert mesa.costo == 28


def test_costo_unitario_con_subproducto():
    madera = Insumo("Madera", "unidad", 20, 0, 10)
    barniz = Insumo("Barniz", "litro", 20, 0, 5)
    base = Producto("Base", "unidad", 0, 0, 1)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)

    base.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(base, 1))
    mesa.agregar_a_BOM(ComponenteBOM(barniz, 2))

    assert base.costo_unitario() == 20
    assert mesa.costo_unitario() == 30


def test_detectar_ciclo_directo():
    producto = Producto("Producto", "unidad", 0, 0, 1)
    producto.agregar_a_BOM(ComponenteBOM(producto, 1))

    assert producto.detectar_ciclo() is True


def test_detectar_ciclo_indirecto():
    primero = Producto("Primero", "unidad", 0, 0, 1)
    segundo = Producto("Segundo", "unidad", 0, 0, 1)
    primero.agregar_a_BOM(ComponenteBOM(segundo, 1))
    segundo.agregar_a_BOM(ComponenteBOM(primero, 1))

    assert primero.detectar_ciclo() is True


def test_no_detectar_ciclo_en_bom_valido():
    madera = Insumo("Madera", "unidad", 20, 0, 10)
    producto = Producto("Mesa", "unidad", 0, 0, 1)
    producto.agregar_a_BOM(ComponenteBOM(madera, 2))

    assert producto.detectar_ciclo() is False
