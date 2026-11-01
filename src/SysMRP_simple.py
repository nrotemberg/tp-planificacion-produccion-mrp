import pickle
from datetime import timedelta
from src.clases_auxiliares import ColaFIFO
from src.manufactura import Colaborador, UnidadTrabajo, PeriodoOperacion
from src.excepciones import EstadoSolicitudError, TipoInvalidoError
from src.bom import GestorBOM
from src.inventario import Inventario
from src.solicitudes import Solicitud


class SistemaMRP:
    def __init__(self):
        self.elementos_produccion = {}
        self.colaboradores = []
        self.unidades_trabajo = []
        self.solicitudes = {}
        self.cola_solicitudes = ColaFIFO()
        self.inventario = Inventario()
        self.bom = GestorBOM()
        self.planes_materiales = {}
        self._periodos_solicitudes = {}
        self._cantidades_a_fabricar = {}
        self._periodos_efectivos = {}
        self._planes_produccion = {}
        self._programaciones_produccion = {}
        self._fabricaciones_realizadas = {}
        self._tareas_fabricacion = {}

    def guardar_pickle(self, ruta):
        with open(ruta, "wb") as archivo:
            pickle.dump(self, archivo)

    @classmethod
    def cargar_pickle(cls, ruta):
        with open(ruta, "rb") as archivo:
            sistema = pickle.load(archivo)
        if not isinstance(sistema, cls):
            raise TypeError("El archivo no contiene un SistemaMRP")
        return sistema

    def agregar_elemento(self, elemento, stock_actual=0, stock_reservado=0):
        if elemento.nombre in self.elementos_produccion:
            return False
        self.elementos_produccion[elemento.nombre] = elemento
        self.inventario.registrar(elemento, stock_actual, stock_reservado)
        return True

    def crear_orden_fabricacion(self, id, articulo, cantidad, **parametros):
        solicitante = parametros.pop("solicitante", None)
        solicitud = Solicitud(id, solicitante, articulo, cantidad, **parametros)
        return self.crear_solicitud(solicitud)

    def crear_solicitud(self, solicitud):
        if self.obtener_solicitud_por_id(solicitud.id) is not None:
            return False
        self.solicitudes[solicitud.id] = solicitud
        self.cola_solicitudes.encolar(solicitud.id)
        return True

    def obtener_solicitud_por_id(self, id_solicitud):
        return self.solicitudes.get(id_solicitud)

    def procesar_siguiente_solicitud(self):
        if not self.cola_solicitudes:
            return False

        id_solicitud = self.cola_solicitudes.ver_primero()
        if not self.reservar_recursos(id_solicitud):
            return False

        self.cola_solicitudes.desencolar()
        return True

    def reservar_recursos(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "creada":
            return False

        plan = self.bom.calcular_plan(solicitud.producto, solicitud.cantidad, self.inventario,)

        faltantes = plan["insumos"]
        disponibles = plan["desde_stock"]

        desde_stock = disponibles.get(solicitud.producto, 0)
        cantidad_a_fabricar = solicitud.cantidad - desde_stock

        requerimientos = dict(faltantes)

        for elemento, cantidad in disponibles.items():
            requerimientos[elemento] = (requerimientos.get(elemento, 0) + cantidad)

        if not self.inventario.hay_stock(requerimientos):
            return False

        # Validar manufactura antes de modificar las reservas.
        programacion = self._calcular_programacion_plan(solicitud, plan,)

        self._validar_conflictos_planes(solicitud.id, programacion,)

        self.inventario.reservar(requerimientos)

        self.planes_materiales[solicitud.id] = (faltantes,disponibles,)
        self._planes_produccion[solicitud.id] = plan
        self._cantidades_a_fabricar[solicitud.id] = cantidad_a_fabricar
        self._programaciones_produccion[solicitud.id] = programacion

        # Mantener la consulta existente del producto principal.
        self._periodos_efectivos[solicitud.id] = programacion.get(solicitud.producto, (),)

        solicitud.cambiar_estado()
        return True

    def fabricar_siguiente_producto(self, id_solicitud):
        """Simula la siguiente fabricación del plan y actualiza el inventario."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "en curso":
            raise EstadoSolicitudError(
                "La solicitud debe estar en curso"
            )

        plan = self.obtener_plan_produccion(id_solicitud)

        realizados = self._fabricaciones_realizadas.setdefault(
            id_solicitud,
            set(),
        )

        producto = next(
            (
                elemento
                for elemento in plan["orden_fabricacion"]
                if elemento not in realizados
            ),
            None,
        )

        # No quedan productos pendientes.
        if producto is None:
            return None

        cantidad = plan["a_fabricar"][producto]

        # Componentes directos consumidos por esta fabricación.
        requerimientos = {}

        for componente in producto.lista_elementos_bom:
            elemento = componente.elemento_produccion

            requerimientos[elemento] = (
                requerimientos.get(elemento, 0)
                + componente.cantidad * cantidad
            )

        # Comprobar todos los componentes antes de ejecutar tareas.
        for elemento, necesaria in requerimientos.items():
            stock = self.inventario.obtener_stock(elemento)

            if (
                stock["actual"] < necesaria
                or stock["reservado"] < necesaria
            ):
                raise EstadoSolicitudError(
                    f"No hay suficientes unidades reservadas "
                    f"de '{elemento.nombre}' para fabricar "
                    f"'{producto.nombre}'"
                )

        programacion = self.obtener_programacion_produccion(
            id_solicitud
        )
        periodos = programacion[producto]
        proceso = producto.proceso_manufactura

        tareas = proceso.iniciar_proceso(
            cantidad,
            list(periodos),
        )

        self._tareas_fabricacion.setdefault(
            id_solicitud,
            {},
        )[producto] = tuple(tareas)

        for tarea in tareas:
            tarea.actualizar_estado("en_curso")
            tarea.finalizar()

        # Transformar los componentes en el producto fabricado.
        self.inventario.consumir(requerimientos)
        self.inventario.agregar_stock(producto, cantidad)

        # La producción nueva queda reservada para esta solicitud.
        self.inventario.reservar({producto: cantidad})

        realizados.add(producto)

        return producto, cantidad

    def consumir_stock(self, id_solicitud):
        """Entrega el pedido cuando terminaron todas sus fabricaciones."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "en curso":
            return False

        if id_solicitud not in self.planes_materiales:
            raise EstadoSolicitudError(
                "La solicitud no tiene un plan reservado"
            )

        plan = self.obtener_plan_produccion(id_solicitud)

        realizados = self._fabricaciones_realizadas.get(
            id_solicitud,
            set(),
        )

        if any(
            producto not in realizados
            for producto in plan["orden_fabricacion"]
        ):
            raise EstadoSolicitudError(
                "Todavía hay productos pendientes de fabricación"
            )

        producto = solicitud.producto
        stock = self.inventario.obtener_stock(producto)

        if (
            stock["actual"] < solicitud.cantidad
            or stock["reservado"] < solicitud.cantidad
        ):
            raise EstadoSolicitudError(
                "No hay suficientes productos reservados para entregar"
            )

        self.inventario.consumir(
            {producto: solicitud.cantidad}
        )

        solicitud.cambiar_estado()
        self.planes_materiales.pop(id_solicitud)

        return True

    def agregar_colaborador(self, colaborador):
        """Registra un colaborador y evita agregar dos veces el mismo objeto."""
        if not isinstance(colaborador, Colaborador):
            raise TipoInvalidoError("El colaborador debe ser una instancia de Colaborador")

        if colaborador in self.colaboradores:
            return False

        self.colaboradores.append(colaborador)
        return True

    def agregar_unidad_trabajo(self, unidad_trabajo):
        """Registra una unidad de trabajo y evita duplicar el mismo objeto."""
        if not isinstance(unidad_trabajo, UnidadTrabajo):
            raise TipoInvalidoError("La unidad de trabajo debe ser una instancia de UnidadTrabajo")

        if unidad_trabajo in self.unidades_trabajo:
            return False

        self.unidades_trabajo.append(unidad_trabajo)
        return True

    def verificar_stock(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None:
            return False
        faltantes, disponibles = self._obtener_plan_materiales(solicitud)
        return self.inventario.hay_stock(faltantes) and self.inventario.hay_stock(
            disponibles
        )

    def iniciar_produccion(self, id_solicitud):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)
        if solicitud is None or solicitud.estado != "planificada":
            return False
        solicitud.cambiar_estado()
        return True

    def programar_solicitud(self, id_solicitud, periodos, producto=None,):
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None or solicitud.estado != "creada":
            raise EstadoSolicitudError(
                "La solicitud debe existir y estar creada"
            )

        if producto is None:
            producto = solicitud.producto

        # Comprobar que el producto pertenece a la BOM del pedido.
        pendientes = [solicitud.producto]
        visitados = set()
        encontrado = False

        while pendientes:
            elemento = pendientes.pop()

            if elemento in visitados:
                continue

            visitados.add(elemento)

            if elemento is producto:
                encontrado = True
                break

            pendientes.extend(
                componente.elemento_produccion
                for componente in elemento.lista_elementos_bom
            )

        if not encontrado:
            raise EstadoSolicitudError(
                "El producto no pertenece a la BOM de la solicitud"
            )

        proceso = getattr(
            producto,
            "proceso_manufactura",
            None,
        )

        if proceso is None or not proceso.tareas:
            raise EstadoSolicitudError(
                "El producto necesita un proceso con tareas"
            )

        if not isinstance(periodos, list) or any(
            not isinstance(periodo, PeriodoOperacion)
            for periodo in periodos
        ):
            raise TipoInvalidoError(
                "Se requiere una lista de PeriodoOperacion"
            )

        if len(periodos) != len(proceso.tareas):
            raise EstadoSolicitudError(
                "Debe existir un período por tarea"
            )

        programacion = self._periodos_solicitudes.setdefault(
            id_solicitud,
            {},
        )

        programacion[producto] = tuple(periodos)

    def obtener_periodos_solicitud(self, id_solicitud, producto=None,):
        """Consulta los períodos del proceso de un producto del pedido."""
        solicitud = self.obtener_solicitud_por_id(id_solicitud)

        if solicitud is None:
            return ()

        if producto is None:
            producto = solicitud.producto

        programacion = self._periodos_solicitudes.get(id_solicitud, {},)

        return programacion.get(producto, ())

    def _validar_conflictos_programacion(self, id_solicitud, tareas, periodos,):
        for otro_id, otros_periodos in self._periodos_efectivos.items():
            if otro_id == id_solicitud:
                continue

            otra_solicitud = self.obtener_solicitud_por_id(otro_id)
            otro_proceso = getattr(
                otra_solicitud.producto,
                "proceso_manufactura",
                None,
            )

            if otro_proceso is None:
                continue

            for tarea, periodo in zip(tareas, periodos):
                for otra_tarea, otro_periodo in zip(
                    otro_proceso.tareas,
                    otros_periodos,
                ):
                    if not periodo.se_solapa_con(otro_periodo):
                        continue

                    if (
                        tarea.unidad_trabajo is not None
                        and tarea.unidad_trabajo is otra_tarea.unidad_trabajo
                    ):
                        raise EstadoSolicitudError(
                            f"La unidad de trabajo "
                            f"'{tarea.unidad_trabajo.nombre}' ya está "
                            "programada en un período superpuesto"
                        )

                    colaboradores_comunes = [
                        colaborador
                        for colaborador in tarea.colaboradores_requeridos
                        if colaborador in otra_tarea.colaboradores_requeridos
                    ]
                    if colaboradores_comunes:
                        colaborador = next(iter(colaboradores_comunes))
                        raise EstadoSolicitudError(
                            f"El colaborador '{colaborador.nombre}' ya está "
                            "programado en un período superpuesto"
                        )

    def finalizar_produccion(self, id_solicitud):
        return self.consumir_stock(id_solicitud)

    def detectar_cuello(self):
        pass

    def _obtener_plan_materiales(self, solicitud):
        """Separa lo que hay que fabricar de lo que ya existe en stock.

        `faltantes` contiene los insumos que `hay_stock` verifica para
        fabricar. `disponibles` contiene los subproductos que ya estaban en
        stock y que tambien deben reservarse para no asignarlos a otra
        solicitud.
        """
        return self.bom.calcular_requerimientos(
            solicitud.producto,
            solicitud.cantidad,
            descontar_stock=True,
            inventario=self.inventario,
        )

    def obtener_plan_produccion(self, id_solicitud):
        """Devuelve una copia del plan reservado para la solicitud."""
        if id_solicitud not in self._planes_produccion:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene un plan de producción"
            )

        plan = self._planes_produccion[id_solicitud]

        return {
            "insumos": dict(plan["insumos"]),
            "desde_stock": dict(plan["desde_stock"]),
            "a_fabricar": dict(plan["a_fabricar"]),
            "orden_fabricacion": tuple(plan["orden_fabricacion"]),
        }

    def calcular_costo_fabricacion(self, id_solicitud):
        """Calcula insumos y operaciones de la fabricación nueva."""
        plan = self.obtener_plan_produccion(id_solicitud)

        costo_insumos = sum(
            elemento.costo_unitario() * cantidad
            for elemento, cantidad in plan["insumos"].items()
        )

        costo_operaciones = sum(
            producto.proceso_manufactura.calcular_costo_operativo()
            * cantidad
            for producto, cantidad in plan["a_fabricar"].items()
        )

        return costo_insumos + costo_operaciones

    def obtener_cantidad_a_fabricar(self, id_solicitud):
        if id_solicitud not in self._cantidades_a_fabricar:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene un plan"
            )

        return self._cantidades_a_fabricar[id_solicitud]

    def obtener_periodos_produccion(self, id_solicitud):
        return self._periodos_efectivos.get(id_solicitud, ())

    def obtener_programacion_produccion(self, id_solicitud):
        """Devuelve una copia de la programación por producto."""
        if id_solicitud not in self._programaciones_produccion:
            raise EstadoSolicitudError(
                "La solicitud todavía no tiene una programación efectiva"
            )

        programacion = self._programaciones_produccion[id_solicitud]

        return {
            producto: tuple(periodos)
            for producto, periodos in programacion.items()
        }

    def _validar_conflictos_planes(self, id_solicitud, programacion,):
        """Comprueba recursos compartidos entre planes programados."""
        programaciones = [
            registrada
            for otro_id, registrada
            in self._programaciones_produccion.items()
            if otro_id != id_solicitud
        ]
        programaciones.append(programacion)

        intervalos_por_recurso = {}

        for registrada in programaciones:
            for producto, periodos in registrada.items():
                proceso = producto.proceso_manufactura

                for tarea, periodo in zip(proceso.tareas, periodos):
                    recursos = list(tarea.colaboradores_requeridos)

                    if tarea.unidad_trabajo is not None:
                        recursos.append(tarea.unidad_trabajo)

                    for recurso in recursos:
                        intervalos_por_recurso.setdefault(
                            recurso,
                            [],
                        ).append(
                            (periodo.inicio, periodo.fin)
                        )

        for recurso, intervalos in intervalos_por_recurso.items():
            intervalos.sort(key=lambda intervalo: intervalo[0])

            for anterior, siguiente in zip(
                intervalos,
                intervalos[1:],
            ):
                if siguiente[0] < anterior[1]:
                    raise EstadoSolicitudError(
                        f"El recurso '{recurso.nombre}' "
                        "tiene trabajos programados superpuestos"
                    )

    def _calcular_programacion_plan(self, solicitud, plan):
        """Calcula los horarios de todos los productos a fabricar."""
        programacion = {}

        for producto in plan["orden_fabricacion"]:
            cantidad = plan["a_fabricar"][producto]

            programacion[producto] = self._calcular_periodos_producto(
                solicitud,
                producto,
                cantidad,
            )

        # Comprobar dependencias entre productos.
        for producto, periodos in programacion.items():
            inicio_producto = min(
                periodo.inicio
                for periodo in periodos
            )

            for componente in producto.lista_elementos_bom:
                pieza = componente.elemento_produccion
                periodos_pieza = programacion.get(pieza, ())

                # Una pieza cubierta por stock no necesita fabricación.
                if not periodos_pieza:
                    continue

                fin_pieza = max(
                    periodo.fin
                    for periodo in periodos_pieza
                )

                if fin_pieza > inicio_producto:
                    raise EstadoSolicitudError(
                        f"El proceso de '{producto.nombre}' "
                        f"comienza antes de terminar '{pieza.nombre}'"
                    )

        # Reunir los intervalos de trabajo de cada recurso.
        intervalos_por_recurso = {}

        for producto, periodos in programacion.items():
            proceso = producto.proceso_manufactura

            for tarea, periodo in zip(proceso.tareas, periodos):
                recursos = list(tarea.colaboradores_requeridos)

                if tarea.unidad_trabajo is not None:
                    recursos.append(tarea.unidad_trabajo)

                for recurso in recursos:
                    intervalos_por_recurso.setdefault(
                        recurso,
                        [],
                    ).append(
                        (periodo.inicio, periodo.fin)
                    )

        # Comparar intervalos consecutivos ordenados por inicio.
        for recurso, intervalos in intervalos_por_recurso.items():
            intervalos.sort(key=lambda intervalo: intervalo[0])

            for anterior, siguiente in zip(
                intervalos,
                intervalos[1:],
            ):
                if siguiente[0] < anterior[1]:
                    raise EstadoSolicitudError(
                        f"El recurso '{recurso.nombre}' tiene "
                        "trabajos superpuestos dentro de la solicitud"
                    )

        return programacion

    def _calcular_periodos_producto(self, solicitud, producto, cantidad,):
        """Calcula los períodos efectivos de un producto sin reservar."""
        if type(cantidad) is not int or cantidad < 0:
            raise TipoInvalidoError(
                "La cantidad a fabricar debe ser un entero no negativo"
            )

        if cantidad == 0:
            return ()

        proceso = getattr(
            producto,
            "proceso_manufactura",
            None,
        )

        if proceso is None or not proceso.tareas:
            raise EstadoSolicitudError(
                f"El producto '{producto.nombre}' "
                "necesita un proceso con tareas"
            )

        ventanas = self.obtener_periodos_solicitud(
            solicitud.id,
            producto,
        )

        if len(ventanas) != len(proceso.tareas):
            raise EstadoSolicitudError(
                f"Faltan períodos para el producto '{producto.nombre}'"
            )

        periodos = []

        for tarea, ventana in zip(proceso.tareas, ventanas):
            horas_necesarias = tarea.tiempo * cantidad

            fin = ventana.inicio + timedelta(
                hours=horas_necesarias
            )

            if fin > ventana.fin:
                raise EstadoSolicitudError(
                    f"El período de '{tarea.nombre}' "
                    f"no alcanza para fabricar {cantidad} "
                    f"unidades de '{producto.nombre}'"
                )

            periodos.append(
                PeriodoOperacion(ventana.inicio, fin)
            )

        proceso.validar_recursos_programados(
            cantidad,
            periodos,
        )

        return tuple(periodos)

    def _calcular_periodos_produccion(self, solicitud, cantidad):
        # Si todo está disponible, no se reserva manufactura.
        if cantidad == 0:
            return []

        proceso = getattr(
            solicitud.producto,
            "proceso_manufactura",
            None,
        )

        # Conserva el comportamiento de los usos existentes sin proceso.
        if proceso is None:
            return []

        ventanas = self.obtener_periodos_solicitud(solicitud.id)

        if len(ventanas) != len(proceso.tareas):
            raise EstadoSolicitudError(
                "Faltan los períodos de la solicitud"
            )

        periodos = []

        for tarea, ventana in zip(proceso.tareas, ventanas):
            fin = ventana.inicio + timedelta(
                hours=tarea.tiempo * cantidad
            )

            if fin > ventana.fin:
                raise EstadoSolicitudError(
                    f"El período de '{tarea.nombre}' no alcanza "
                    f"para {cantidad} unidades"
                )

            periodos.append(
                PeriodoOperacion(ventana.inicio, fin)
            )

        proceso.validar_recursos_programados(cantidad, periodos)

        self._validar_conflictos_programacion(
            solicitud.id,
            proceso.tareas,
            periodos,
        )

        return periodos