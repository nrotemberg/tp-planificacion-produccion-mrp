import json
from datetime import datetime

from src.SysMRP_simple import SistemaMRP
from src.elementos import Insumo, Producto
from src.excepciones import MRPError, ErrorConfiguracion
from src.manufactura import (
    Colaborador,
    UnidadTrabajo,
    ProcesoManufactura,
    TareaDefinida,
    PeriodoOperacion,
)

def leer_configuracion(ruta):
    """Lee el JSON y comprueba su estructura principal."""
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            datos = json.load(archivo)

    except OSError as error:
        raise ErrorConfiguracion(
            f"No se pudo abrir el archivo '{ruta}': {error}"
        ) from error

    except (json.JSONDecodeError, UnicodeError) as error:
        raise ErrorConfiguracion(
            f"El archivo '{ruta}' no contiene un JSON válido: {error}"
        ) from error

    if not isinstance(datos, dict):
        raise ErrorConfiguracion(
            "La configuración debe ser un objeto JSON"
        )

    if type(datos.get("version")) is not int or datos["version"] != 1:
        raise ErrorConfiguracion(
            "La configuración debe indicar una versión igual a 1"
        )

    secciones = (
        "elementos",
        "colaboradores",
        "unidades_trabajo",
        "procesos",
        "solicitudes",
    )

    campos_permitidos = {"version", *secciones}
    desconocidos = datos.keys() - campos_permitidos

    if desconocidos:
        raise ErrorConfiguracion(
            f"Campos desconocidos: {', '.join(sorted(desconocidos))}"
        )

    for seccion in secciones:
        if seccion not in datos:
            raise ErrorConfiguracion(
                f"Falta la sección '{seccion}'"
            )

        if not isinstance(datos[seccion], list):
            raise ErrorConfiguracion(
                f"La sección '{seccion}' debe ser una lista"
            )

    return datos

def _crear_elementos(datos, sistema):
    """Crea los artículos y los relaciona con sus identificadores externos."""
    elementos_por_id = {}

    for posicion, dato in enumerate(datos["elementos"]):
        contexto = f"elementos[{posicion}]"

        if not isinstance(dato, dict):
            raise ErrorConfiguracion(
                f"{contexto}: debe ser un objeto"
            )

        obligatorios = {"id", "tipo", "nombre", "unidad_medida", "costo"}
        permitidos = obligatorios | {"stock_actual", "bom"}

        if obligatorios - dato.keys():
            raise ErrorConfiguracion(
                f"{contexto}: faltan campos obligatorios"
            )

        if dato.keys() - permitidos:
            raise ErrorConfiguracion(
                f"{contexto}: contiene campos desconocidos"
            )

        identificador = dato["id"]

        if not isinstance(identificador, str) or not identificador.strip():
            raise ErrorConfiguracion(
                f"{contexto}: el id debe ser un texto no vacío"
            )

        if identificador in elementos_por_id:
            raise ErrorConfiguracion(
                f"ID de elemento duplicado: '{identificador}'"
            )

        if dato["tipo"] == "insumo":
            clase = Insumo
        elif dato["tipo"] == "producto":
            clase = Producto
        else:
            raise ErrorConfiguracion(
                f"{contexto}: el tipo debe ser 'insumo' o 'producto'"
            )

        stock = dato.get("stock_actual", 0)

        if type(stock) is not int or stock < 0:
            raise ErrorConfiguracion(
                f"{contexto}: el stock debe ser un entero no negativo"
            )

        try:
            elemento = clase(
                dato["nombre"],
                dato["unidad_medida"],
                dato["costo"],
            )

            agregado = sistema.agregar_elemento(elemento, stock)

        except MRPError as error:
            raise ErrorConfiguracion(
                f"{contexto}: {error}"
            ) from error

        if not agregado:
            raise ErrorConfiguracion(
                f"Nombre de elemento duplicado: '{dato['nombre']}'"
            )

        elementos_por_id[identificador] = elemento

    return elementos_por_id


def _cargar_bom(datos, elementos_por_id):
    """Vincula los artículos una vez que todos fueron creados."""
    for dato in datos["elementos"]:
        identificador = dato["id"]
        elemento = elementos_por_id[identificador]
        componentes = dato.get("bom", [])

        if not isinstance(componentes, list):
            raise ErrorConfiguracion(
                f"La BOM de '{identificador}' debe ser una lista"
            )

        if isinstance(elemento, Insumo) and componentes:
            raise ErrorConfiguracion(
                f"El insumo '{identificador}' no puede tener BOM"
            )

        for componente in componentes:
            if (
                not isinstance(componente, dict)
                or set(componente) != {"elemento_id", "cantidad"}
            ):
                raise ErrorConfiguracion(
                    f"BOM de '{identificador}': cada componente debe "
                    "tener elemento_id y cantidad"
                )

            referencia = componente["elemento_id"]

            if (
                not isinstance(referencia, str)
                or referencia not in elementos_por_id
            ):
                raise ErrorConfiguracion(
                    f"BOM de '{identificador}': "
                    f"elemento inexistente '{referencia}'"
                )

            try:
                elemento.construir_bom_manual(
                    elementos_por_id[referencia],
                    componente["cantidad"],
                )

            except MRPError as error:
                raise ErrorConfiguracion(
                    f"BOM de '{identificador}': {error}"
                ) from error


def cargar_sistema_desde_json(ruta):
    """Construye y programa un sistema nuevo sin ejecutar producción."""
    datos = leer_configuracion(ruta)
    sistema = SistemaMRP()

    elementos_por_id = _crear_elementos(datos, sistema)
    _cargar_bom(datos, elementos_por_id)

    colaboradores_por_id = _cargar_colaboradores(datos, sistema)
    unidades_por_id = _cargar_unidades_trabajo(datos, sistema)

    tareas_por_producto = _cargar_procesos(
        datos,
        elementos_por_id,
        colaboradores_por_id,
        unidades_por_id,
    )

    _cargar_solicitudes(
        datos,
        sistema,
        elementos_por_id,
        tareas_por_producto,
    )

    return sistema


def _validar_registro(dato, obligatorios, opcionales, registrados, contexto):
    if not isinstance(dato, dict):
        raise ErrorConfiguracion(
            f"{contexto}: debe ser un objeto"
        )

    if obligatorios - dato.keys():
        raise ErrorConfiguracion(
            f"{contexto}: faltan campos obligatorios"
        )

    if dato.keys() - (obligatorios | opcionales):
        raise ErrorConfiguracion(
            f"{contexto}: contiene campos desconocidos"
        )

    identificador = dato["id"]

    if not isinstance(identificador, str) or not identificador.strip():
        raise ErrorConfiguracion(
            f"{contexto}: el id debe ser un texto no vacío"
        )

    if identificador in registrados:
        raise ErrorConfiguracion(
            f"{contexto}: ID duplicado '{identificador}'"
        )

    nombre = dato["nombre"]

    if not isinstance(nombre, str) or not nombre.strip():
        raise ErrorConfiguracion(
            f"{contexto}: el nombre debe ser un texto no vacío"
        )

    return identificador


def _cargar_colaboradores(datos, sistema):
    colaboradores_por_id = {}

    for posicion, dato in enumerate(datos["colaboradores"]):
        contexto = f"colaboradores[{posicion}]"

        identificador = _validar_registro(
            dato,
            {"id", "nombre", "costo_por_hora"},
            {"habilidades"},
            colaboradores_por_id,
            contexto,
        )

        habilidades = dato.get("habilidades", [])

        if not isinstance(habilidades, list) or any(
            not isinstance(habilidad, str) or not habilidad.strip()
            for habilidad in habilidades
        ):
            raise ErrorConfiguracion(
                f"{contexto}: habilidades debe ser una lista de textos"
            )

        try:
            colaborador = Colaborador(
                dato["nombre"],
                dato["costo_por_hora"],
                habilidades,
            )

            sistema.agregar_colaborador(colaborador)

        except MRPError as error:
            raise ErrorConfiguracion(
                f"{contexto}: {error}"
            ) from error

        colaboradores_por_id[identificador] = colaborador

    return colaboradores_por_id


def _cargar_unidades_trabajo(datos, sistema):
    unidades_por_id = {}

    for posicion, dato in enumerate(datos["unidades_trabajo"]):
        contexto = f"unidades_trabajo[{posicion}]"

        identificador = _validar_registro(
            dato,
            {
                "id",
                "nombre",
                "capacidad_max_produccion",
                "costo_fijo",
                "capacidad_colaboradores",
            },
            set(),
            unidades_por_id,
            contexto,
        )

        capacidad = dato["capacidad_max_produccion"]
        capacidad_colaboradores = dato["capacidad_colaboradores"]

        if type(capacidad) is not int or capacidad <= 0:
            raise ErrorConfiguracion(
                f"{contexto}: capacidad_max_produccion "
                "debe ser un entero positivo"
            )

        if (
            type(capacidad_colaboradores) is not int
            or capacidad_colaboradores < 0
        ):
            raise ErrorConfiguracion(
                f"{contexto}: capacidad_colaboradores "
                "debe ser un entero no negativo"
            )

        try:
            unidad = UnidadTrabajo(
                dato["nombre"],
                capacidad,
                dato["costo_fijo"],
                capacidad_colaboradores,
            )

            sistema.agregar_unidad_trabajo(unidad)

        except MRPError as error:
            raise ErrorConfiguracion(
                f"{contexto}: {error}"
            ) from error

        unidades_por_id[identificador] = unidad

    return unidades_por_id


def _buscar_referencia(registro, identificador, contexto):
    """Busca un objeto existente mediante su ID externo."""
    if (
        not isinstance(identificador, str)
        or identificador not in registro
    ):
        raise ErrorConfiguracion(
            f"{contexto}: identificador inexistente '{identificador}'"
        )

    return registro[identificador]


def _cargar_procesos(
    datos,
    elementos_por_id,
    colaboradores_por_id,
    unidades_por_id,
):
    """Crea procesos y devuelve las tareas de cada producto por ID."""
    procesos_por_id = {}
    tareas_por_producto = {}

    for posicion, dato in enumerate(datos["procesos"]):
        contexto = f"procesos[{posicion}]"

        if not isinstance(dato, dict) or set(dato) != {
            "id", "producto_id", "tareas"
        }:
            raise ErrorConfiguracion(
                f"{contexto}: debe contener id, producto_id y tareas"
            )

        identificador = dato["id"]

        if not isinstance(identificador, str) or not identificador.strip():
            raise ErrorConfiguracion(
                f"{contexto}: el id debe ser un texto no vacío"
            )

        if identificador in procesos_por_id:
            raise ErrorConfiguracion(
                f"{contexto}: ID de proceso duplicado '{identificador}'"
            )

        producto_id = dato["producto_id"]
        producto = _buscar_referencia(
            elementos_por_id, producto_id, contexto
        )

        if not isinstance(producto, Producto):
            raise ErrorConfiguracion(
                f"{contexto}: el proceso debe pertenecer a un producto"
            )

        filas_tareas = dato["tareas"]

        if not isinstance(filas_tareas, list) or not filas_tareas:
            raise ErrorConfiguracion(
                f"{contexto}: tareas debe ser una lista no vacía"
            )

        try:
            proceso = ProcesoManufactura(producto)
        except MRPError as error:
            raise ErrorConfiguracion(
                f"{contexto}: {error}"
            ) from error

        tareas_por_id = {}

        for indice, fila in enumerate(filas_tareas):
            contexto_tarea = f"{contexto}.tareas[{indice}]"

            tarea_id = _validar_registro(
                fila,
                {"id", "nombre", "tiempo"},
                {
                    "unidad_trabajo_id",
                    "colaboradores_ids",
                    "habilidades_requeridas",
                    "predecesoras_ids",
                },
                tareas_por_id,
                contexto_tarea,
            )

            unidad_id = fila.get("unidad_trabajo_id")
            unidad = None

            if unidad_id is not None:
                unidad = _buscar_referencia(
                    unidades_por_id, unidad_id, contexto_tarea
                )

            colaboradores_ids = fila.get("colaboradores_ids", [])

            if not isinstance(colaboradores_ids, list):
                raise ErrorConfiguracion(
                    f"{contexto_tarea}: colaboradores_ids debe ser una lista"
                )

            colaboradores = [
                _buscar_referencia(
                    colaboradores_por_id, referencia, contexto_tarea
                )
                for referencia in colaboradores_ids
            ]

            try:
                tarea = TareaDefinida(
                    fila["nombre"],
                    fila["tiempo"],
                    unidad,
                    colaboradores,
                    fila.get("habilidades_requeridas", []),
                )

                tarea.validar_colaboradores_requeridos(colaboradores)
                proceso.agregar_tarea(tarea)

            except MRPError as error:
                raise ErrorConfiguracion(
                    f"{contexto_tarea}: {error}"
                ) from error

            tareas_por_id[tarea_id] = tarea

        # Todas las tareas ya existen: ahora vinculamos sus dependencias.
        posiciones = {
            fila["id"]: indice
            for indice, fila in enumerate(filas_tareas)
        }

        for fila in filas_tareas:
            tarea_id = fila["id"]
            predecesoras = fila.get("predecesoras_ids", [])

            if not isinstance(predecesoras, list):
                raise ErrorConfiguracion(
                    f"{contexto}: predecesoras_ids debe ser una lista"
                )

            for referencia in predecesoras:
                predecesora = _buscar_referencia(
                    tareas_por_id, referencia, contexto
                )

                if posiciones[referencia] >= posiciones[tarea_id]:
                    raise ErrorConfiguracion(
                        f"{contexto}: la predecesora '{referencia}' "
                        f"debe aparecer antes de '{tarea_id}'"
                    )

                try:
                    tareas_por_id[tarea_id].agregar_subtarea(predecesora)
                except MRPError as error:
                    raise ErrorConfiguracion(
                        f"{contexto}: {error}"
                    ) from error

        procesos_por_id[identificador] = proceso
        tareas_por_producto[producto_id] = tareas_por_id

    return tareas_por_producto


def _leer_fecha(valor, contexto):
    """Interpreta una fecha ISO expresada en hora local."""
    if not isinstance(valor, str):
        raise ErrorConfiguracion(
            f"{contexto}: la fecha debe ser un texto"
        )

    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError as error:
        raise ErrorConfiguracion(
            f"{contexto}: fecha inválida '{valor}'"
        ) from error

    if fecha.tzinfo is not None:
        raise ErrorConfiguracion(
            f"{contexto}: usá hora local sin zona horaria"
        )

    return fecha


def _cargar_solicitudes(
    datos,
    sistema,
    elementos_por_id,
    tareas_por_producto,
):
    solicitudes_registradas = set()

    for posicion, dato in enumerate(datos["solicitudes"]):
        contexto = f"solicitudes[{posicion}]"

        if not isinstance(dato, dict):
            raise ErrorConfiguracion(
                f"{contexto}: debe ser un objeto"
            )

        obligatorios = {"id", "producto_id", "cantidad", "periodos"}
        permitidos = obligatorios | {"solicitante"}

        if obligatorios - dato.keys() or dato.keys() - permitidos:
            raise ErrorConfiguracion(
                f"{contexto}: hay campos faltantes o desconocidos"
            )

        identificador = dato["id"]

        if not isinstance(identificador, str) or not identificador.strip():
            raise ErrorConfiguracion(
                f"{contexto}: el id debe ser un texto no vacío"
            )

        if identificador in solicitudes_registradas:
            raise ErrorConfiguracion(
                f"{contexto}: ID duplicado '{identificador}'"
            )

        producto_id = dato["producto_id"]
        producto = _buscar_referencia(
            elementos_por_id, producto_id, contexto
        )

        tareas_por_id = tareas_por_producto.get(producto_id)

        if tareas_por_id is None:
            raise ErrorConfiguracion(
                f"{contexto}: el producto no tiene proceso de manufactura"
            )

        filas_periodos = dato["periodos"]

        if not isinstance(filas_periodos, list):
            raise ErrorConfiguracion(
                f"{contexto}: periodos debe ser una lista"
            )

        periodos_por_tarea = {}

        for indice, fila in enumerate(filas_periodos):
            contexto_periodo = f"{contexto}.periodos[{indice}]"

            if not isinstance(fila, dict) or set(fila) != {
                "tarea_id", "inicio", "fin"
            }:
                raise ErrorConfiguracion(
                    f"{contexto_periodo}: debe contener "
                    "tarea_id, inicio y fin"
                )

            tarea_id = fila["tarea_id"]
            _buscar_referencia(
                tareas_por_id, tarea_id, contexto_periodo
            )

            if tarea_id in periodos_por_tarea:
                raise ErrorConfiguracion(
                    f"{contexto_periodo}: período repetido "
                    f"para '{tarea_id}'"
                )

            inicio = _leer_fecha(fila["inicio"], contexto_periodo)
            fin = _leer_fecha(fila["fin"], contexto_periodo)

            try:
                periodos_por_tarea[tarea_id] = PeriodoOperacion(
                    inicio, fin
                )
            except MRPError as error:
                raise ErrorConfiguracion(
                    f"{contexto_periodo}: {error}"
                ) from error

        if set(periodos_por_tarea) != set(tareas_por_id):
            raise ErrorConfiguracion(
                f"{contexto}: debe existir un período por cada tarea"
            )

        # Conserva el orden de las tareas del proceso,
        # independientemente del orden de los períodos en el JSON.
        periodos = [
            periodos_por_tarea[tarea_id]
            for tarea_id in tareas_por_id
        ]

        solicitante = dato.get("solicitante", "Sin especificar")

        if not isinstance(solicitante, str) or not solicitante.strip():
            raise ErrorConfiguracion(
                f"{contexto}: solicitante debe ser un texto no vacío"
            )

        try:
            agregado = sistema.crear_orden_fabricacion(
                identificador,
                producto,
                dato["cantidad"],
                solicitante=solicitante,
            )

            if not agregado:
                raise ErrorConfiguracion(
                    f"{contexto}: la solicitud ya existe"
                )

            sistema.programar_solicitud(identificador, periodos)

        except MRPError as error:
            raise ErrorConfiguracion(
                f"{contexto}: {error}"
            ) from error

        solicitudes_registradas.add(identificador)


