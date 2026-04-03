from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from modelos.base import Base
from comun.enums import NivelLog

class LogEjecucion(Base):
    __tablename__ = "logs_ejecucion"

    id_log    = Column(Integer, primary_key=True, autoincrement=True)
    id_imagen = Column(Integer, ForeignKey("imagenes.id_imagen"), nullable=False)
    id_nodo   = Column(Integer, nullable=True)
    mensaje   = Column(String, nullable=False)
    nivel     = Column(SAEnum(NivelLog), default=NivelLog.INFO)
    timestamp = Column(DateTime, default=datetime.now)

    imagen = relationship("Imagen", back_populates="logs")
