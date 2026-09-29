import pytest

from src.bom import GestorBOM
from src.elementos import ComponenteBOM, Insumo, Producto
from src.excepciones import BOMCiclicaError


def test_calcular_requerimientos_bom_simple():
    madera = Insumo("Madera", "unidad", 100, 0, 5)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(mesa,3)
    assert faltantes == {madera: 6}
    assert disponibles == {}

def test_calcular_requerimientos_bom_anidada():
    madera = Insumo("Madera", "unidad", 100, 0, 5)
    base = Producto("Base", "unidad", 0, 0, 1)
    base.agregar_a_BOM(ComponenteBOM(madera, 3))
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(base, 2))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(mesa,2)
    assert faltantes == {madera: 12}
    assert disponibles == {}

def test_calcular_requerimientos_suma_elementos_repetidos():
    acero = Insumo("Acero", "kg", 100, 0, 5)
    pieza_a = Producto("Pieza A", "unidad", 0, 0, 1)
    pieza_a.agregar_a_BOM(ComponenteBOM(acero, 2))
    pieza_b = Producto("Pieza B", "unidad", 0, 0, 1)
    pieza_b.agregar_a_BOM(ComponenteBOM(acero, 3))
    producto = Producto("Producto", "unidad", 0, 0, 1)
    producto.agregar_a_BOM(ComponenteBOM(pieza_a, 1))
    producto.agregar_a_BOM(ComponenteBOM(pieza_b, 1))
    gestor = GestorBOM()
    faltantes, _ = gestor.calcular_requerimientos(producto, 2)
    assert faltantes == {acero: 10}

def test_calcular_requerimientos_utiliza_stock_de_subproducto():
    aluminio = Insumo("Aluminio", "unidad", 100, 0, 5)
    motor = Producto("Motor", "unidad", 4, 0, 1)
    motor.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    auto = Producto("Auto", "unidad", 0, 0, 1)
    auto.agregar_a_BOM(ComponenteBOM(motor, 1))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(auto, 10, descontar_stock=True)
    assert disponibles == {motor: 4}
    assert faltantes == {aluminio: 12}

def test_calcular_requerimientos_no_descuenta_stock_si_no_se_pide():
    aluminio = Insumo("Aluminio", "unidad", 100, 0, 5)
    motor = Producto("Motor", "unidad", 4, 0, 1)
    motor.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    auto = Producto("Auto", "unidad", 0, 0, 1)
    auto.agregar_a_BOM(ComponenteBOM(motor, 1))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(auto, 10)
    assert disponibles == {}
    assert faltantes == {aluminio: 20}

def test_calcular_requerimientos_detecta_ciclo_directo():
    producto = Producto("Producto", "unidad", 0, 0, 1)
    producto.agregar_a_BOM(ComponenteBOM(producto, 1))
    gestor = GestorBOM()
    with pytest.raises(BOMCiclicaError):
        gestor.calcular_requerimientos(producto, 1)

def test_calcular_requerimientos_detecta_ciclo_indirecto():
    producto_a = Producto("A", "unidad", 0, 0, 1)
    producto_b = Producto("B", "unidad", 0, 0, 1)
    producto_a.agregar_a_BOM(ComponenteBOM(producto_b, 1))
    producto_b.agregar_a_BOM(ComponenteBOM(producto_a, 1))
    gestor = GestorBOM()
    with pytest.raises(BOMCiclicaError):
        gestor.calcular_requerimientos(producto_a, 1)

def test_arbol_texto_muestra_bom():
    madera = Insumo("Madera", "unidad", 100, 0, 5)
    clavos = Insumo("Clavos", "unidad", 100, 0, 1)
    mesa = Producto("Mesa", "unidad", 0, 0, 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(clavos, 4))
    gestor = GestorBOM()
    resultado = gestor.arbol_texto(mesa, 2)
    assert resultado == (
        "Mesa x 2\n"
        "+-- Madera x 4\n"
        "`-- Clavos x 8")
    