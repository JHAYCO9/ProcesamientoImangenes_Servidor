from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
from modelos.base import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario     = Column(Integer, primary_key=True, autoincrement=True)
    nombre         = Column(String, nullable=False)
    email          = Column(String, unique=True, nullable=False)
    password_hash  = Column(String, nullable=False)
    fecha_registro = Column(DateTime, default=datetime.now)
    activo         = Column(Boolean, default=True)

    solicitudes = relationship("SolicitudLote", back_populates="usuario")

    def set_password(self, raw: str) -> None:
        self.password_hash = hashlib.sha256(raw.encode()).hexdigest()

    def verificar_password(self, raw: str) -> bool:
        return self.password_hash == hashlib.sha256(raw.encode()).hexdigest()

    def get_solicitudes(self) -> list:
        return self.solicitudes
