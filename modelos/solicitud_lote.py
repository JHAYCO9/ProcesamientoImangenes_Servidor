from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from modelos.base import Base
from comun.enums import EstadoLote

class SolicitudLote(Base):
    __tablename__ = "solicitudes_lote"

    id_lote              = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario           = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    fecha_recepcion      = Column(DateTime, default=datetime.now)
    estado               = Column(SAEnum(EstadoLote), default=EstadoLote.PENDIENTE)
    total_imagenes       = Column(Integer, default=0)
    imagenes_completadas = Column(Integer, default=0)

    usuario  = relationship("Usuario", back_populates="solicitudes")
    imagenes = relationship("Imagen", back_populates="lote")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.total_imagenes is None:
            self.total_imagenes = 0
        if self.imagenes_completadas is None:
            self.imagenes_completadas = 0
        if self.estado is None:
            self.estado = EstadoLote.PENDIENTE
        if self.fecha_recepcion is None:
            self.fecha_recepcion = datetime.now()

    def get_progreso(self) -> float:
        if not self.total_imagenes:
            return 0.0
        return (self.imagenes_completadas / self.total_imagenes) * 100

    def agregar_imagen(self, img) -> None:
        self.imagenes.append(img)
        self.total_imagenes += 1

    def get_imagenes(self) -> list:
        return self.imagenes

    def esta_completo(self) -> bool:
        return self.imagenes_completadas == self.total_imagenes