import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import main as m


def test_costo_no_puede_ser_cero_o_negativo():
    with pytest.raises(ValueError):
        m.Insumo("Agua", "L", 10, 0, 0)

    with pytest.raises(ValueError):
        m.Insumo("Aceite", "L", 10, 0, -5)
    print("OK: test_costo_no_puede_ser_cero_o_negativo")


def test_elemento_produccion_crea_datos_basicos():
    insumo = m.Insumo("Harina", "kg", 50, 10, 25)

    assert insumo.nombre == "Harina"
    assert insumo.unidad_medida == "kg"
    assert insumo.stock_total == 50
    assert insumo.stock_reservado == 10
    assert insumo.costo == 25
    print("OK: test_elemento_produccion_crea_datos_basicos")


def test_insumo_get_costo_y_set_costo():
    insumo = m.Insumo("Azucar", "kg", 30, 0, 15)

    assert insumo.get_costo() == 15

    insumo.set_costo(18)
    assert insumo.get_costo() == 18

    with pytest.raises(ValueError):
        insumo.set_costo(0)

    with pytest.raises(ValueError):
        insumo.set_costo(-1)
    print("OK: test_insumo_get_costo_y_set_costo")


def test_insumo_actualizar_costo():
    insumo = m.Insumo("Sal", "kg", 20, 0, 8)

    insumo.actualizar_costo(10)
    assert insumo.get_costo() == 10

    with pytest.raises(ValueError):
        insumo.actualizar_costo(0)
    print("OK: test_insumo_actualizar_costo")


def test_componente_bom_validacion_cantidad():
    insumo = m.Insumo("Huevo", "unidad", 20, 0, 12)
    componente = m.ComponenteBOM(insumo, 3)

    assert componente.elemento_produccion is insumo
    assert componente.cantidad == 3

    componente.set_cantidad(5)
    assert componente.cantidad == 5

    with pytest.raises(ValueError):
        componente.set_cantidad(0)

    with pytest.raises(ValueError):
        componente.set_cantidad(-2)
    print("OK: test_componente_bom_validacion_cantidad")


def test_producto_agregar_a_bom_y_costo_unitario():
    harina = m.Insumo("Harina", "kg", 50, 0, 20)
    azucar = m.Insumo("Azucar", "kg", 20, 0, 10)
    pan = m.Producto("Pan", "kg", 100, 0, 15)

    pan.agregar_a_bom(m.ComponenteBOM(harina, 2))
    pan.agregar_a_bom(m.ComponenteBOM(azucar, 3))

    assert len(pan.lista_elementos_bom) == 2
    assert pan.costo_unitario() == 70
    assert pan.costo == 70
    print("OK: test_producto_agregar_a_bom_y_costo_unitario")


def test_producto_con_subproducto_suma_costos():
    huevo = m.Insumo("Huevo", "unidad", 20, 0, 12)
    azucar = m.Insumo("Azucar", "kg", 20, 0, 10)

    bagazo = m.Producto("Bagazo", "kg", 10, 0, 5)
    bagazo.agregar_a_bom(m.ComponenteBOM(huevo, 2))
    bagazo.agregar_a_bom(m.ComponenteBOM(azucar, 1))

    pan = m.Producto("Pan", "kg", 50, 0, 12)
    pan.agregar_a_bom(m.ComponenteBOM(huevo, 1))
    pan.agregar_a_bom(m.ComponenteBOM(bagazo, 1))

    assert bagazo.costo_unitario() == 34
    assert pan.costo_unitario() == 46
    print("OK: test_producto_con_subproducto_suma_costos")


def test_proceso_manufactura_crea_datos_basicos():
    pan = m.Producto("Pan", "kg", 50, 0, 80)
    proceso = m.ProcesoManufactura(pan)

    assert proceso.producto is pan
    assert proceso.tareas_requeridas == []
    print("OK: test_proceso_manufactura_crea_datos_basicos")


def test_tarea_definida_crea_datos_basicos():
    tarea = m.TareaDefinida("Mezclar", 2.5, "horas", 3, ["habilidad1", "habilidad2"])

    assert tarea.nombre == "Mezclar"
    assert tarea.tiempo == 2.5
    assert tarea.unidad_trabajo == "horas"
    assert tarea.colaboradores_requeridos == 3
    assert tarea.habilidades_requeridas == ["habilidad1", "habilidad2"]
    print("OK: test_tarea_definida_crea_datos_basicos")


def test_tarea_en_curso_crea_datos_basicos():
    tarea_base = m.TareaDefinida("Coccion", 1.5, "horas", 2, ["habilidad1", "habilidad2"])
    tarea = m.TareaEnCurso("Coccion_1", tarea_base, "pendiente")

    assert tarea.nombre == "Coccion_1"
    assert tarea.tarea_base is tarea_base
    assert tarea.estado == "pendiente"
    assert tarea.colaboradores_asignados == []
    assert tarea.unidades_trabajo_asignadas == []
    print("OK: test_tarea_en_curso_crea_datos_basicos")


def test_unidad_trabajo_crea_datos_basicos():
    ut = m.UnidadTrabajo("Horno", 100, 5000, 4)

    assert ut.nombre == "Horno"
    assert ut.capacidad_max_produccion == 100
    assert ut.costo_fijo == 5000
    assert ut.capacidad_colaboradores == 4
    assert ut.periodos_operacion == []
    assert ut.colaboradores_activos == []
    assert ut.maquinas_disponibles == []
    print("OK: test_unidad_trabajo_crea_datos_basicos")


def test_colaborador_crea_datos_basicos():
    colaborador = m.Colaborador("Ana", 250, ["habilidad1", "habilidad2"])

    assert colaborador.nombre == "Ana"
    assert colaborador.costo_por_hora == 250
    assert colaborador.periodos_operacion == []
    assert colaborador.habilidades == ["habilidad1", "habilidad2"]
    print("OK: test_colaborador_crea_datos_basicos")


def test_periodo_operacion_crea_datos_basicos():
    periodo = m.PeriodoOperacion(8, 12)

    assert periodo.inicio == 8
    assert periodo.fin == 12
    print("OK: test_periodo_operacion_crea_datos_basicos")


def test_solicitud_crea_datos_basicos():
    pan = m.Producto("Pan", "kg", 50, 0, 80)
    solicitud = m.Solicitud(1, "Deposito", "planificada", pan, 10)

    assert solicitud.id == 1
    assert solicitud.solicitante == "Deposito"
    assert solicitud.fase == "planificada"
    assert solicitud.producto is pan
    assert solicitud.cantidad == 10
    print("OK: test_solicitud_crea_datos_basicos")


def test_hola_mundo():
    assert m.hola_mundo() == "hola_mundo"
    print("OK: test_hola_mundo")



test_hola_mundo()
test_costo_no_puede_ser_cero_o_negativo()
test_elemento_produccion_crea_datos_basicos()
test_insumo_get_costo_y_set_costo()
test_insumo_actualizar_costo()
test_componente_bom_validacion_cantidad()
test_producto_agregar_a_bom_y_costo_unitario()
test_producto_con_subproducto_suma_costos()
test_proceso_manufactura_crea_datos_basicos()
test_tarea_definida_crea_datos_basicos()
test_tarea_en_curso_crea_datos_basicos()
test_unidad_trabajo_crea_datos_basicos()
test_colaborador_crea_datos_basicos()
test_periodo_operacion_crea_datos_basicos()
test_solicitud_crea_datos_basicos()