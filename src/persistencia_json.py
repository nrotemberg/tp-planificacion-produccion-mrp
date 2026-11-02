import json
from datetime import datetime

from src.excepciones import ErrorConfiguracion, MRPError
from src.manufactura import PeriodoOperacion


def guardar_estado(ruta, sistema):
    elementos = sistema.elementos_produccion
    estado = {
        "version": 1,
        "inventario": {
            nombre: dict(sistema.inventario.obtener_stock(elemento))
            for nombre, elemento in elementos.items()
        },
        "solicitudes": [
            {
                "id": solicitud.id,
                "producto": solicitud.producto.nombre,
                "cantidad": solicitud.cantidad,
                "solicitante": solicitud.solicitante,
                "estado": solicitud.estado,
                "inicio": (
                    solicitud.inicio_planificacion.isoformat()
                    if solicitud.inicio_planificacion
                    else None
                ),
            }
            for solicitud in sistema.solicitudes.values()
        ],
        "cola": list(_valores_cola(sistema.cola_solicitudes)),
        "planes": {},
    }

    for solicitud_id, plan in sistema._planes_produccion.items():
        estado["planes"][solicitud_id] = {
            "insumos": _mapa_a_json(plan["insumos"]),
            "desde_stock": _mapa_a_json(plan["desde_stock"]),
            "a_fabricar": _mapa_a_json(plan["a_fabricar"]),
            "orden_fabricacion": [
                elemento.nombre for elemento in plan["orden_fabricacion"]
            ],
            "materiales": [
                _mapa_a_json(mapa)
                for mapa in sistema.planes_materiales.get(
                    solicitud_id,
                    ({}, {}),
                )
            ],
            "cantidad_a_fabricar": sistema._cantidades_a_fabricar[
                solicitud_id
            ],
            "programacion": {
                producto.nombre: [
                    {
                        "inicio": periodo.inicio.isoformat(),
                        "fin": periodo.fin.isoformat(),
                    }
                    for periodo in periodos
                ]
                for producto, periodos
                in sistema._programaciones_produccion[solicitud_id].items()
            },
            "productos_fabricados": [
                producto.nombre
                for producto in sistema._fabricaciones_realizadas.get(
                    solicitud_id,
                    set(),
                )
            ],
            "fin_estimado": sistema._finalizaciones_estimadas[
                solicitud_id
            ].isoformat(),
        }

    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(estado, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
    except OSError as error:
        raise ErrorConfiguracion(
            f"No se pudo guardar el estado '{ruta}': {error}"
        ) from error


def cargar_estado(ruta, sistema):
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            estado = json.load(archivo)
    except FileNotFoundError:
        return False
    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        raise ErrorConfiguracion(
            f"No se pudo leer el estado '{ruta}': {error}"
        ) from error

    try:
        _restaurar_estado(estado, sistema)
    except (KeyError, TypeError, ValueError, MRPError) as error:
        raise ErrorConfiguracion(
            f"El estado '{ruta}' no es válido: {error}"
        ) from error
    return True


def _restaurar_estado(estado, sistema):
    if not isinstance(estado, dict) or set(estado) != {
        "version",
        "inventario",
        "solicitudes",
        "cola",
        "planes",
    }:
        raise ValueError("debe contener version, inventario, solicitudes, cola y planes")
    if estado["version"] != 1:
        raise ValueError("versión de estado no compatible")

    elementos = sistema.elementos_produccion
    if not isinstance(estado["inventario"], dict):
        raise ValueError("inventario debe ser un objeto")
    for nombre, cantidades in estado["inventario"].items():
        if nombre not in elementos or not isinstance(cantidades, dict):
            raise ValueError(f"elemento de inventario desconocido: {nombre}")
        if set(cantidades) != {"actual", "reservado"}:
            raise ValueError(f"stock inválido para '{nombre}'")
        actual = cantidades["actual"]
        reservado = cantidades["reservado"]
        if (
            type(actual) is not int
            or type(reservado) is not int
            or reservado < 0
            or actual < reservado
        ):
            raise ValueError(f"cantidades inválidas para '{nombre}'")
        sistema.inventario.stock[elementos[nombre]].update(cantidades)

    if not isinstance(estado["solicitudes"], list):
        raise ValueError("solicitudes debe ser una lista")
    for fila in estado["solicitudes"]:
        if not isinstance(fila, dict) or set(fila) != {
            "id", "producto", "cantidad", "solicitante", "estado", "inicio"
        }:
            raise ValueError("registro de solicitud inválido")
        producto = elementos.get(fila["producto"])
        if producto is None:
            raise ValueError(f"producto desconocido: {fila['producto']}")
        solicitud_id = fila["id"]
        if solicitud_id in sistema.solicitudes:
            raise ValueError(f"solicitud duplicada: {solicitud_id}")
        if not sistema.crear_orden_fabricacion(
            solicitud_id,
            producto,
            fila["cantidad"],
            solicitante=fila["solicitante"],
        ):
            raise ValueError(f"no se pudo restaurar {solicitud_id}")
        solicitud = sistema.solicitudes[solicitud_id]
        if fila["estado"] not in (
            "creada", "planificada", "en curso", "finalizada"
        ):
            raise ValueError(f"estado inválido en {solicitud_id}")
        solicitud.estado = fila["estado"]
        if fila["inicio"] is not None:
            solicitud.inicio_planificacion = datetime.fromisoformat(
                fila["inicio"]
            )

    if not isinstance(estado["cola"], list):
        raise ValueError("cola debe ser una lista")
    sistema.cola_solicitudes = type(sistema.cola_solicitudes)()
    for solicitud_id in estado["cola"]:
        if solicitud_id not in sistema.solicitudes:
            raise ValueError(f"solicitud de cola desconocida: {solicitud_id}")
        sistema.cola_solicitudes.encolar(solicitud_id)

    if not isinstance(estado["planes"], dict):
        raise ValueError("planes debe ser un objeto")
    for solicitud_id, fila in estado["planes"].items():
        _restaurar_plan(solicitud_id, fila, sistema, elementos)


def _restaurar_plan(solicitud_id, fila, sistema, elementos):
    if solicitud_id not in sistema.solicitudes:
        raise ValueError(f"plan de solicitud desconocida: {solicitud_id}")

    def resolver(nombre):
        if nombre not in elementos:
            raise ValueError(f"elemento del plan desconocido: {nombre}")
        return elementos[nombre]

    plan = {
        clave: _mapa_desde_json(fila[clave], resolver)
        for clave in ("insumos", "desde_stock", "a_fabricar")
    }
    plan["orden_fabricacion"] = tuple(
        resolver(nombre) for nombre in fila["orden_fabricacion"]
    )
    sistema._planes_produccion[solicitud_id] = plan
    sistema.planes_materiales[solicitud_id] = tuple(
        _mapa_desde_json(mapa, resolver)
        for mapa in fila["materiales"]
    )
    sistema._cantidades_a_fabricar[solicitud_id] = fila[
        "cantidad_a_fabricar"
    ]
    sistema._programaciones_produccion[solicitud_id] = {
        resolver(nombre): tuple(
            PeriodoOperacion(
                datetime.fromisoformat(periodo["inicio"]),
                datetime.fromisoformat(periodo["fin"]),
            )
            for periodo in periodos
        )
        for nombre, periodos in fila["programacion"].items()
    }
    solicitud = sistema.solicitudes[solicitud_id]
    sistema._periodos_efectivos[solicitud_id] = (
        sistema._programaciones_produccion[solicitud_id].get(
            solicitud.producto,
            (),
        )
    )
    sistema._fabricaciones_realizadas[solicitud_id] = {
        resolver(nombre) for nombre in fila["productos_fabricados"]
    }
    sistema._finalizaciones_estimadas[solicitud_id] = datetime.fromisoformat(
        fila["fin_estimado"]
    )


def _mapa_a_json(mapa):
    return {elemento.nombre: cantidad for elemento, cantidad in mapa.items()}


def _mapa_desde_json(mapa, resolver):
    if not isinstance(mapa, dict):
        raise ValueError("un plan de materiales debe ser un objeto")
    return {resolver(nombre): cantidad for nombre, cantidad in mapa.items()}


def _valores_cola(cola):
    nodo = cola.primero
    while nodo is not None:
        yield nodo.dato
        nodo = nodo.siguiente
