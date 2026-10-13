import pytest

from src.elementos import ElementoProduccion, Insumo, Producto, ComponenteBOM
from src.excepciones import CostoInvalidoError, TipoInvalidoError


def crear_insumo(nombre="Madera", costo=10):
    return Insumo(nombre, "unidad", costo)


def test_crear_elemento_y_obtener_costo():
    elemento = ElementoProduccion("Elemento", "unidad", 25)

    assert elemento.nombre == "Elemento"
    assert elemento.unidad_medida == "unidad"
    assert elemento.costo_unitario() == 25


def test_set_costo_rechaza_valores_invalidos():
    elemento = ElementoProduccion("Elemento", "unidad", 25)

    elemento.set_costo(30)
    assert elemento.costo == 30

    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(0)
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(-1)
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo("30")


def test_construir_bom_manual_y_agregar_a_bom():
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 1)

    producto.construir_bom_manual(madera, 2)
    producto.agregar_a_BOM(ComponenteBOM(madera, 3))

    assert len(producto.lista_elementos_bom) == 2
    assert producto.lista_elementos_bom[0].elemento_produccion is madera


def test_agregar_a_bom_rechaza_tipo_incorrecto():
    producto = Producto("Mesa", "unidad", 1)

    with pytest.raises(TipoInvalidoError):
        producto.agregar_a_BOM("incorrecto")


def test_imprimir_bom(capsys):
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 1)
    producto.construir_bom_manual(madera, 2)

    producto.imprimir_bom()
    salida = capsys.readouterr().out

    assert "Mesa" in salida
    assert "Madera" in salida
