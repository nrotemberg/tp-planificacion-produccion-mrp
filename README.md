# Sistema de Planificación de la Producción (MRP) - TecnoMecánica ITBA S.A.


## Descripción del Proyecto


Este repositorio contiene el código para el nuevo sistema de planificación de la producción (MRP) de **TecnoMecánica ITBA S.A.**, una empresa dedicada a la fabricación de maquinaria industrial. El objetivo principal de este sistema es automatizar los procesos de producción, gestionar eficientemente la explosión de materiales (Bill of Materials - BOM), reducir los cuellos de botella y optimizar la asignación de recursos mediante la gestión de solicitudes de fabricación.


## Arquitectura y Diagrama de Clases


El sistema ha sido modelado utilizando Programación Orientada a Objetos (POO), garantizando modularidad, escalabilidad y flexibilidad. Tal como se detalla en el diagrama de arquitectura, el sistema se divide en las siguientes entidades principales:


### 1. Elementos de Producción y BOM
* **`ElementoProduccion`**: Clase padre que engloba a todos los artículos físicos.
* **`Insumo`**: Hereda de `ElementoProduccion`. Representa los materiales básicos que se compran y no tienen proceso de fabricación.
* **`Producto`**: Hereda de `ElementoProduccion`. Representa sub-ensambles o productos terminados. Contiene una BOM expuesta como colección de solo lectura; sus componentes se agregan mediante `agregar_a_BOM`, que valida los ciclos.
* **`ComponenteBOM`**: Define la relación estructural; indica qué cantidad exacta de un `ElementoProduccion` se requiere para armar un `Producto`.


### 2. Procesos de Manufactura
* **`ProcesoManufactura`**: Define la secuencia de tareas necesarias para transformar los componentes en un producto final.
* **`TareaDefinida`**: Plantilla de un paso de producción. Especifica el tiempo base, la unidad de trabajo necesaria y los colaboradores requeridos.
* **`TareaEnCurso`**: Representa la ejecución real de una tarea, con estado actualizado, unidades de trabajo y colaboradores asignados. Además, mantiene un registro de las tareas realizadas.


### 3. Gestión de Recursos y Tiempos
* **`UnidadTrabajo`**: Estaciones de trabajo. Poseen capacidades máximas de producción, límites de colaboradores y costos fijos.
* **`Colaborador`**: Empleados con costo por hora, habilidades y períodos ocupados.
* **`PeriodoOperacion`**: Intervalos calculados para las tareas planificadas; permiten detectar ocupaciones superpuestas.


### 4. Flujo de Solicitudes
* **`Solicitud`**: Maneja el ciclo de vida de una orden de fabricación. Gestiona las fases (creada, planificada, en curso), verificando el stock disponible, reservando los materiales y finalmente iniciando y cerrando la producción para registrar el consumo.

### 5. Simplificación del flujo
La explosión de la BOM se concentra en `bom.py`, dentro de la clase `GestorBOM`.
Su método `explotar` recorre todos los niveles y devuelve un diccionario plano
de insumos y cantidades requeridas.

`Inventario`, definido en `inventario.py`, utiliza esos requerimientos para verificar, reservar y consumir stock. El stock no pertenece a `ElementoProduccion`: se guarda en `Inventario.stock`, usando cada elemento como clave y registrando las cantidades `actual` y `reservado`. `SistemaMRP` coordina el flujo de la solicitud sin repetir la lógica recursiva; la persistencia del inventario y los pedidos queda en el archivo de estado.

El flujo básico se mantiene:

```text
creada -> planificada -> en curso -> finalizada
```

Una solicitud sólo reserva materiales cuando está creada, sólo inicia producción cuando está planificada y sólo consume stock cuando está en curso. El menú procesa una solicitud completa por vez, desde el frente de la cola FIFO; si no se puede planificar, permanece en la cola para reintentar.

Al crear una solicitud se elige un producto final, se indica la cantidad y el solicitante. Los productos intermedios que forman parte de la BOM no aparecen como pedidos independientes. Al procesar la solicitud, el sistema toma la fecha y hora actual, calcula cuántas unidades debe fabricar según el stock disponible y genera automáticamente los períodos de las tareas. Cada tarea dura `tiempo × cantidad`; respeta sus predecesoras y los productos requeridos por la BOM. Tareas que usan recursos distintos pueden superponerse; si comparten una unidad de trabajo o un colaborador, se ubican una después de la otra. El calendario es continuo (24/7), sin turnos ni pausas, y se informa la hora estimada de finalización.

La configuración fija usa el formato JSON versión 3 y vive en
`datos/empresa.json`: define elementos, colaboradores, unidades de trabajo y
procesos. El inventario y las solicitudes se guardan por separado en
`datos/empresa_estado.json`, para no mezclar la definición de la empresa con
los datos que cambian durante el uso. Si el archivo de estado no existe, el
sistema lo crea con inventario vacío y sin solicitudes. Al salir y
después de cada acción del menú, el estado se guarda; al volver a iniciar, se
restauran el inventario, la cola FIFO y el progreso de las solicitudes.

Para usar otro archivo de configuración, se busca el estado junto a él con el
mismo nombre base y el sufijo `_estado.json`. Las solicitudes se crean desde
el menú y no se cargan en la configuración fija.

## Ejecución

Desde la raíz del proyecto, se inicia el sistema con:

```bash
python main.py
```

Opcionalmente, se puede indicar otro archivo de configuración JSON versión 3:

```bash
python main.py ruta/a/empresa.json
```

El archivo de estado se crea junto a la configuración indicada, con el mismo
nombre base y el sufijo `_estado.json`. El menú permite:

| Opción | Acción |
|---|---|
| 1 | Procesar la siguiente solicitud de la cola FIFO, de principio a fin. |
| 2 | Consultar las solicitudes y sus estados. |
| 3 | Consultar stock actual, reservado y libre. |
| 4 | Agregar 100 unidades de cada insumo. |
| 5 | Crear una solicitud para un producto fabricable. |
| 6 | Consultar las unidades de trabajo más ocupadas. |
| 7 | Consultar el historial de tareas de la sesión. |
| 8 | Consultar las tareas definidas en la configuración. |
| 9 | Consultar las unidades de trabajo configuradas. |
| 10 | Consultar los colaboradores configurados. |
| 11 | Guardar el estado y salir. |

Para ejecutar los tests automatizados:

```bash
python -m pytest
```



## Reglas de Negocio Clave


El diseño del software asegura el cumplimiento de las siguientes reglas operativas:
- **Cantidades Válidas:** Todo inventario y solicitud se maneja con valores enteros y positivos.
- **Prevención de Ciclos BOM:** Un producto nunca puede depender de sí mismo (directa o indirectamente) para ser fabricado.
- **Cálculo de Costos Unitarios:** El costo de un artículo fabricado se calcula dinámicamente sumando el costo de sus insumos y el costo operativo por unidad de su `ProcesoManufactura` (uso de máquinas y horas de colaboradores). Cada producto puede tener un único proceso asociado.
- **Verificación Estricta de Inventario:** No se puede iniciar (fase 'en curso') una `Solicitud` sin contar con el stock físico de sus dependencias.
- **Detección de Cuellos de Botella:** Capacidad de analizar restricciones (falta de materiales o saturación de unidades de trabajo/colaboradores) simulando la carga de trabajo pendiente.