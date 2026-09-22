class MRPError(Exception):
    """Excepción base del sistema MRP."""
    pass


class CantidadInvalidaError(MRPError):
    """Se levanta cuando una cantidad no es válida."""
    pass


class CostoInvalidoError(MRPError):
    """Se levanta cuando el costo no cumple la validación del negocio."""
    pass


class TipoInvalidoError(MRPError):
    """Se levanta cuando un tipo esperado no coincide con el recibido."""
    pass


class ElementoDuplicadoError(MRPError):
    """Se levanta cuando se intenta registrar dos veces el mismo elemento."""
    pass


class ElementoNoEncontradoError(MRPError):
    """Se levanta cuando un elemento buscado no existe en el sistema."""
    pass


class SolicitudDuplicadaError(MRPError):
    """Se levanta cuando ya existe una solicitud con el mismo identificador."""
    pass


class SolicitudNoEncontradaError(MRPError):
    """Se levanta cuando la solicitud solicitada no existe."""
    pass


class EstadoSolicitudError(MRPError):
    """Se levanta cuando una solicitud está en un estado inválido para la acción."""
    pass


class StockInsuficienteError(MRPError):
    """Se levanta cuando no hay stock disponible para cubrir el requerimiento."""
    pass


class BOMCiclicaError(MRPError):
    """Se levanta cuando la estructura de la BOM contiene un ciclo."""
    pass


class HabilidadRequeridaError(MRPError):
    """Se levanta cuando falta una habilidad requerida para la tarea."""
    pass


class RecursosInsuficientesError(MRPError):
    """Se levanta cuando no hay suficientes colaboradores o recursos."""
    pass


class PeriodoOcupadoError(MRPError):
    """Se levanta cuando un periodo de operación se solapa con un recurso ocupado."""
    pass


class ColaboradorNoDisponibleError(MRPError):
    """Se levanta cuando un colaborador no está disponible en el periodo indicado."""
    pass


class SolicitudNoEncontradaErrorConId(SolicitudNoEncontradaError):
    """Error específico para solicitudes inexistentes con detalle del ID."""

    def __init__(self, solicitud_id):
        super().__init__(f"No existe la solicitud {solicitud_id}")

__all__ = [
    "MRPError",
    "CantidadInvalidaError",
    "CostoInvalidoError",
    "TipoInvalidoError",
    "ElementoDuplicadoError",
    "ElementoNoEncontradoError",
    "SolicitudDuplicadaError",
    "SolicitudNoEncontradaError",
    "SolicitudNoEncontradaErrorConId",
    "EstadoSolicitudError",
    "StockInsuficienteError",
    "BOMCiclicaError",
    "HabilidadRequeridaError",
    "RecursosInsuficientesError",
    "PeriodoOcupadoError",
    "ColaboradorNoDisponibleError",
]
