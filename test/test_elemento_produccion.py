import pytest

from src.elementos import ElementoProduccion, Insumo, Producto, ComponenteBOM
from src.excepciones import (
    BOMCiclicaError,
    CostoInvalidoError,
    TipoInvalidoError,
)


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
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(True)
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(float("inf"))
    with pytest.raises(CostoInvalidoError):
        elemento.set_costo(float("nan"))


@pytest.mark.parametrize(
    ("nombre", "unidad_medida"),
    [("", "unidad"), ("  ", "unidad"), ("Mesa", ""), ("Mesa", None)],
)
def test_elemento_rechaza_nombre_o_unidad_invalidos(nombre, unidad_medida):
    with pytest.raises(TipoInvalidoError):
        ElementoProduccion(nombre, unidad_medida, 10)


def test_construir_bom_manual_y_agregar_a_bom():
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 1)

    producto.construir_bom_manual(madera, 2)
    producto.agregar_a_BOM(ComponenteBOM(madera, 3))

    assert len(producto.lista_elementos_bom) == 2
    assert producto.lista_elementos_bom[0].elemento_produccion is madera


def test_lista_bom_no_permite_modificacion_directa():
    producto = Producto("Mesa", "unidad", 1)

    with pytest.raises(AttributeError):
        producto.lista_elementos_bom.append(ComponenteBOM(crear_insumo(), 1))


def test_agregar_a_bom_rechaza_tipo_incorrecto():
    producto = Producto("Mesa", "unidad", 1)

    with pytest.raises(TipoInvalidoError):
        producto.agregar_a_BOM("incorrecto")


def test_agregar_a_bom_rechaza_ciclo_directo():
    producto = Producto("Mesa", "unidad", 1)

    with pytest.raises(BOMCiclicaError):
        producto.agregar_a_BOM(ComponenteBOM(producto, 1))

    assert producto.lista_elementos_bom == ()


def test_agregar_a_bom_rechaza_ciclo_indirecto():
    primero = Producto("Primero", "unidad", 1)
    segundo = Producto("Segundo", "unidad", 1)
    primero.agregar_a_BOM(ComponenteBOM(segundo, 1))

    with pytest.raises(BOMCiclicaError):
        segundo.agregar_a_BOM(ComponenteBOM(primero, 1))

    assert segundo.lista_elementos_bom == ()


def test_imprimir_bom_detecta_ciclos_existentes():
    producto = Producto("Mesa", "unidad", 1)
    producto._lista_elementos_bom.append(ComponenteBOM(producto, 1))

    with pytest.raises(BOMCiclicaError):
        producto.imprimir_bom()


def test_imprimir_bom(capsys):
    madera = crear_insumo()
    producto = Producto("Mesa", "unidad", 1)
    producto.construir_bom_manual(madera, 2)

    producto.imprimir_bom()
    salida = capsys.readouterr().out

    assert "Mesa" in salida
    assert "Madera" in salida
