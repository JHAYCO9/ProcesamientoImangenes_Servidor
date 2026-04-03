from abc import ABC, abstractmethod

class IServicioImagenes(ABC):

    @abstractmethod
    def login(self, email: str, password: str) -> str:
        pass

    @abstractmethod
    def registrar(self, nombre: str, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def enviar_lote(self, token: str, nombres: list, datos: list, transfs: list) -> str:
        pass

    @abstractmethod
    def consultar_progreso(self, token: str, id_lote: int) -> dict:
        pass

    @abstractmethod
    def descargar_imagen(self, token: str, id_imagen: int) -> bytes:
        pass

    @abstractmethod
    def descargar_lote_zip(self, token: str, id_lote: int) -> bytes:
        pass

    @abstractmethod
    def obtener_historial(self, token: str) -> list:
        pass

    @abstractmethod
    def listar_nodos(self, token: str) -> list:
        pass
