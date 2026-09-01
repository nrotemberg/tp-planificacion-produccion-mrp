# Sistema de Planificación de la Producción (MRP) - TecnoMecánica ITBA S.A.


## Descripción del Proyecto


Este repositorio contiene el código para el nuevo sistema de planificación de la producción (MRP) de **TecnoMecánica ITBA S.A.**, una empresa dedicada a la fabricación de maquinaria industrial. El objetivo principal de este sistema es automatizar los procesos de producción, gestionar eficientemente la explosión de materiales (Bill of Materials - BOM), reducir los cuellos de botella y optimizar la asignación de recursos mediante la gestión de solicitudes de fabricación.


## Arquitectura y Diagrama de Clases


El sistema ha sido modelado utilizando Programación Orientada a Objetos (POO), garantizando modularidad, escalabilidad y flexibilidad. Tal como se detalla en el diagrama de arquitectura (`image_f02b0e.png`), el sistema se divide en las siguientes entidades principales:


### 1. Elementos de Producción y BOM
* **`ElementoProduccion`**: Clase padre que engloba a todos los artículos físicos.
* **`Insumo`**: Hereda de `ElementoProduccion`. Representa los materiales básicos que se compran y no tienen proceso de fabricación.
* **`Producto`**: Hereda de `ElementoProduccion`. Representa sub-ensambles o productos terminados. Contiene una lista de elementos que lo componen (BOM).
* **`ComponenteBOM`**: Define la relación estructural; indica qué cantidad exacta de un `ElementoProduccion` se requiere para armar un `Producto`.


### 2. Procesos de Manufactura
* **`ProcesoManufactura`**: Define la secuencia de tareas necesarias para transformar los componentes en un producto final.
* **`TareaDefinida`**: Plantilla de un paso de producción. Especifica el tiempo base, la unidad de trabajo necesaria y los colaboradores requeridos.
* **`TareaEnCurso`**: Representa la ejecución real de una tarea, con estado actualizado, unidades de trabajo y colaboradores asignados. Además, mantiene un registro de las tareas realizadas.


### 3. Gestión de Recursos y Tiempos
* **`UnidadTrabajo`**: Estaciones de trabajo. Poseen capacidades máximas de producción, límites de colaboradores y costos fijos.
* **`Colaborador`**: Empleados de la planta con un costo por hora y disponibilidad ligada a períodos de trabajo.
* **`PeriodoOperacion`**: Bloques temporales (inicio y fin) que controlan cuándo un recurso o colaborador está disponible.


### 4. Flujo de Solicitudes
* **`Solicitud`**: Maneja el ciclo de vida de una orden de fabricación. Gestiona las fases (creada, planificada, en curso), verificando el stock disponible, reservando los materiales y finalmente iniciando y cerrando la producción para registrar el consumo.


## Reglas de Negocio Clave


El diseño del software asegura el cumplimiento de las siguientes reglas operativas:
- **Cantidades Válidas:** Todo inventario y solicitud se maneja con valores enteros y positivos.
- **Prevención de Ciclos BOM:** Un producto nunca puede depender de sí mismo (directa o indirectamente) para ser fabricado.
- **Cálculo de Costos Unitarios:** El costo de un artículo fabricado se calcula dinámicamente sumando el costo de sus insumos y el costo de su `ProcesoManufactura` (uso de máquinas y horas de colaboradores).
- **Verificación Estricta de Inventario:** No se puede iniciar (fase 'en curso') una `Solicitud` sin contar con el stock físico de sus dependencias.
- **Detección de Cuellos de Botella:** Capacidad de analizar restricciones (falta de materiales o saturación de unidades de trabajo/colaboradores) simulando la carga de trabajo pendiente.