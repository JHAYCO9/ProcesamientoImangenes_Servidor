from enum import Enum

class EstadoLote(Enum):
    PENDIENTE  = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    ERROR      = "ERROR"

class EstadoImagen(Enum):
    PENDIENTE  = "PENDIENTE"
    PROCESANDO = "PROCESANDO"
    LISTO      = "LISTO"
    ERROR      = "ERROR"

class EstadoNodo(Enum):
    ACTIVO   = "ACTIVO"
    INACTIVO = "INACTIVO"
    ERROR    = "ERROR"

class NivelLog(Enum):
    INFO  = "INFO"
    WARN  = "WARN"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
