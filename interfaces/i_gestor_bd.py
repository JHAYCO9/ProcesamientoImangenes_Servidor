from abc import ABC, abstractmethod

class IGestorBD(ABC):

    @abstractmethod
    def guardar(self, entidad) -> None:
        pass

    @abstractmethod
    def obtener(self, modelo, filtros: dict):
        pass

    @abstractmethod
    def actualizar(self, modelo, id: int, datos: dict) -> None:
        pass

    @abstractmethod
    def eliminar(self, modelo, id: int) -> None:
        pass
