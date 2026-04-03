from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from modelos.base import Base
from comun.enums import EstadoImagen

class Imagen(Base):
    __tablename__ = "imagenes"

    id_imagen         = Column(Integer, primary_key=True, autoincrement=True)
    id_lote           = Column(Integer, ForeignKey("solicitudes_lote.id_lote"), nullable=False)
    id_nodo           = Column(Integer, ForeignKey("nodos.id_nodo"), nullable=True)
    nombre_archivo    = Column(String, nullable=False)
    ruta_original     = Column(String, nullable=False)
    ruta_resultado    = Column(String, nullable=True)
    formato_original  = Column(String, nullable=False)
    formato_resultado = Column(String, nullable=True)
    estado            = Column(SAEnum(EstadoImagen), default=EstadoImagen.PENDIENTE)
    fecha_recepcion   = Column(DateTime, default=datetime.now)
    fecha_conversion  = Column(DateTime, nullable=True)
    tamano_bytes      = Column(Integer, nullable=True)

    lote = relationship("SolicitudLote", back_populates="imagenes")
    logs = relationship("LogEjecucion", back_populates="imagen")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.transformaciones_pendientes = []  # no se persiste en BD, solo en memoria

    def get_nodo(self, nodo) -> None:
        self.id_nodo = nodo.id_nodo

    def get_transformaciones(self) -> list:
        return []

    def agregar_imagen(self, img) -> None:
        pass

    def aplicar_transformacion(self, t) -> None:
        pass

    def set_resultado(self, nodo, formato: str) -> None:
        self.id_nodo          = nodo.id_nodo
        self.formato_resultado = formato
        self.fecha_conversion  = datetime.now()
        self.estado            = EstadoImagen.LISTO
