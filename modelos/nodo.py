from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from datetime import datetime
from modelos.base import Base
from comun.enums import EstadoNodo

class Nodo(Base):
    __tablename__ = "nodos"

    id_nodo          = Column(Integer, primary_key=True, autoincrement=True)
    identificador    = Column(String, unique=True, nullable=False)
    direccion_red    = Column(String, nullable=False)
    puerto_pyro5     = Column(Integer, nullable=False)
    estado           = Column(SAEnum(EstadoNodo), default=EstadoNodo.ACTIVO)
    ultima_actividad = Column(DateTime, default=datetime.now)
    trabajos_activos = Column(Integer, default=0)

    def get_proxy_pyro5(self):
        import Pyro5.api
        uri = f"PYRO:nodo_procesador@{self.direccion_red}:{self.puerto_pyro5}"
        return Pyro5.api.Proxy(uri)

    def esta_disponible(self) -> bool:
        return self.estado == EstadoNodo.ACTIVO and self.trabajos_activos < 5

    def incrementar_trabajo(self) -> None:
        self.trabajos_activos += 1

    def decrementar_trabajo(self) -> None:
        if self.trabajos_activos > 0:
            self.trabajos_activos -= 1
