import pytest

from src.elementos import ComponenteBOM, Insumo, Producto
from src.excepciones import BOMCiclicaError, ElementoDuplicadoError
from src.manufactura import ProcesoManufactura, TareaDefinida, UnidadTrabajo


def test_costo_unitario_con_insumos():
    madera = Insumo("Madera", "unidad", 10)
    clavos = Insumo("Clavos", "unidad", 2)
    mesa = Producto("Mesa", "unidad", 1)

    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(clavos, 4))

    assert mesa.costo_unitario() == 28
    assert mesa.costo == 28


def test_costo_unitario_con_subproducto():
    madera = Insumo("Madera", "unidad", 10)
    barniz = Insumo("Barniz", "litro", 5)
    base = Producto("Base", "unidad", 1)
    mesa = Producto("Mesa", "unidad", 1)

    base.agregar_a_BOM(ComponenteBOM(madera, 2))
    mesa.agregar_a_BOM(ComponenteBOM(base, 1))
    mesa.agregar_a_BOM(ComponenteBOM(barniz, 2))

    assert base.costo_unitario() == 20
    assert mesa.costo_unitario() == 30


def test_costo_unitario_suma_costo_operativo_del_proceso():
    madera = Insumo("Madera", "unidad", 10)
    mesa = Producto("Mesa", "unidad", 1)
    mesa.agregar_a_BOM(ComponenteBOM(madera, 2))
    proceso = ProcesoManufactura(mesa)
    proceso.agregar_tarea(
        TareaDefinida(
            "Corte",
            1,
            UnidadTrabajo("Sierra", 10, 50, 1),
            [],
            [],
        )
    )

    assert mesa.costo_unitario() == 70


def test_producto_rechaza_un_segundo_proceso_manufactura():
    producto = Producto("Mesa", "unidad", 1)
    ProcesoManufactura(producto)

    with pytest.raises(ElementoDuplicadoError, match="ya tiene un proceso"):
        ProcesoManufactura(producto)


def test_detectar_ciclo_directo():
    producto = Producto("Producto", "unidad", 1)
    producto._lista_elementos_bom.append(ComponenteBOM(producto, 1))

    assert producto.detectar_ciclo() is True


def test_detectar_ciclo_indirecto():
    primero = Producto("Primero", "unidad", 1)
    segundo = Producto("Segundo", "unidad", 1)
    primero._lista_elementos_bom.append(ComponenteBOM(segundo, 1))
    segundo._lista_elementos_bom.append(ComponenteBOM(primero, 1))

    assert primero.detectar_ciclo() is True


def test_no_detectar_ciclo_en_bom_valido():
    madera = Insumo("Madera", "unidad", 10)
    producto = Producto("Mesa", "unidad", 1)
    producto.agregar_a_BOM(ComponenteBOM(madera, 2))

    assert producto.detectar_ciclo() is False
