import pytest

from src.elementos import ElementoProduccion, Insumo, Producto, ComponenteBOM
from src.excepciones import CostoInvalidoError, TipoInvalidoError


def crear_insumo(nombre="Madera", stock=20, reservado=0, costo=10):
    return Insumo(nombre, "unidad", stock, reservado, costo)


def test_crear_elemento_y_obtener_costo():
    elemento = ElementoProduccion("Elemento", "unidad", 10, 2, 25)

    assert elemento.nombre == "Elemento"
    assert elemento.unidad_medida == "unidad"
    assert elemento.stock_total == 10
    assert elemento.stock_reservado == 2
    assert elemento.costo_unitario() == 25


def test_set_costo_rechaza_valores_invalidos():
    elemento = ElementoProduccion("Elemento", "unidad", 10, 0, 25)

    elemento.set_costo(30)
    assert elemento.costo == 30

    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(0)
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(-1)
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo("30")


def test_hay_stock_suficiente_considera_reservado():
    elemento = crear_insumo(stock=10, reservado=3)

    assert elemento.hay_stock_suficiente(7) is True
    assert elemento.hay_stock_suficiente(8) is False


def test_construir_bom_manual_y_agregar_a_bom():
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 0, 0, 1)

    producto.construir_bom_manual(madera, 2)
    producto.agregar_a_BOM(ComponenteBOM(madera, 3))

    assert len(producto.lista_elementos_bom) == 2
    assert producto.lista_elementos_bom[0].elemento_produccion is madera


def test_agregar_a_bom_rechaza_tipo_incorrecto():
    producto = Producto("Mesa", "unidad", 0, 0, 1)

    with pytest.raises(TipoInvalidoError):
        producto.agregar_a_BOM("incorrecto")


def test_imprimir_bom_e_imprimir_stock(capsys):
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 0, 0, 1)
    producto.construir_bom_manual(madera, 2)

    producto.imprimir_bom()
    ElementoProduccion.imprimir_stock([madera, producto])
    salida = capsys.readouterr().out

    assert "Mesa" in salida
    assert "Madera" in salida
    assert "Cantidad" in salida
