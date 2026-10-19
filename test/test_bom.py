import pytest

from src.bom import GestorBOM
from src.elementos import ComponenteBOM, Insumo, Producto
from src.excepciones import BOMCiclicaError
from src.inventario import Inventario


def test_calcular_requerimientos_bom_simple():
    madera = Insumo("Madera", "unidad", 5)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(mesa,3)
    assert faltantes == {madera: 6}
    assert disponibles == {}

def test_calcular_requerimientos_bom_anidada():
    madera = Insumo("Madera", "unidad", 5)
    base = Producto("Base", "unidad", 1)
    base.agregar_a_BOM(ComponenteBOM(madera, 3))
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(base, 2))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(mesa,2)
    assert faltantes == {madera: 12}
    assert disponibles == {}

def test_calcular_requerimientos_suma_elementos_repetidos():
    acero = Insumo("Acero", "kg", 5)
    pieza_a = Producto("Pieza A", "unidad", 1)
    pieza_a.agregar_a_BOM(ComponenteBOM(acero, 2))
    pieza_b = Producto("Pieza B", "unidad", 1)
    pieza_b.agregar_a_BOM(ComponenteBOM(acero, 3))
    producto = Producto("Producto", "unidad", 1)
    producto.agregar_a_BOM(ComponenteBOM(pieza_a, 1))
    producto.agregar_a_BOM(ComponenteBOM(pieza_b, 1))
    gestor = GestorBOM()
    faltantes, _ = gestor.calcular_requerimientos(producto, 2)
    assert faltantes == {acero: 10}

def test_calcular_requerimientos_utiliza_stock_de_subproducto():
    aluminio = Insumo("Aluminio", "unidad", 5)
    motor = Producto("Motor", "unidad", 1)
    motor.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    auto = Producto("Auto", "unidad", 1)
    auto.agregar_a_BOM(ComponenteBOM(motor, 1))
    inventario = Inventario()
    inventario.registrar(aluminio, 100)
    inventario.registrar(motor, 4)
    inventario.registrar(auto)
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(
        auto, 10, descontar_stock=True, inventario=inventario
    )
    assert disponibles == {motor: 4}
    assert faltantes == {aluminio: 12}

def test_calcular_requerimientos_no_descuenta_stock_si_no_se_pide():
    aluminio = Insumo("Aluminio", "unidad", 5)
    motor = Producto("Motor", "unidad", 1)
    motor.agregar_a_BOM(ComponenteBOM(aluminio, 2))
    auto = Producto("Auto", "unidad", 1)
    auto.agregar_a_BOM(ComponenteBOM(motor, 1))
    gestor = GestorBOM()
    faltantes, disponibles = gestor.calcular_requerimientos(auto, 10)
    assert disponibles == {}
    assert faltantes == {aluminio: 20}

def test_calcular_requerimientos_detecta_ciclo_directo():
    producto = Producto("Producto", "unidad", 1)
    producto._lista_elementos_bom.append(ComponenteBOM(producto, 1))
    gestor = GestorBOM()
    with pytest.raises(BOMCiclicaError):
        gestor.calcular_requerimientos(producto, 1)

def test_calcular_requerimientos_detecta_ciclo_indirecto():
    producto_a = Producto("A", "unidad", 1)
    producto_b = Producto("B", "unidad", 1)
    producto_a._lista_elementos_bom.append(ComponenteBOM(producto_b, 1))
    producto_b._lista_elementos_bom.append(ComponenteBOM(producto_a, 1))
    gestor = GestorBOM()
    with pytest.raises(BOMCiclicaError):
        gestor.calcular_requerimientos(producto_a, 1)

def test_arbol_texto_muestra_bom():
    madera = Insumo("Madera", "unidad", 5)
    clavos = Insumo("Clavos", "unidad", 1)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(clavos, 4))
    gestor = GestorBOM()
    resultado = gestor.arbol_texto(mesa, 2)
    assert resultado == (
        "Mesa x 2\n"
        "+-- Madera x 4\n"
        "`-- Clavos x 8")
    