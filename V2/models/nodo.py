import json
import Pyro5.api


class Nodo:

    def __init__(self, id_nodo: int, identificador: str, direccion: str, puerto: int):
        self.id            = id_nodo
        self.identificador = identificador
        self.direccion     = direccion
        self.puerto        = puerto
        self.carga         = 0
        self.activo        = True

    def disponible(self) -> bool:
        return self.activo

    def get_proxy(self):
        uri = f"PYRO:nodo_procesador@{self.direccion}:{self.puerto}"
        return Pyro5.api.Proxy(uri)

    def ping(self) -> bool:
        try:
            with self.get_proxy() as proxy:
                return proxy.ping()
        except Exception:
            self.activo = False
            return False

    def get_carga(self) -> int:
        try:
            with self.get_proxy() as proxy:
                self.carga  = proxy.get_trabajos_pendientes()
                self.activo = True
                return self.carga
        except Exception:
            self.activo = False
            return 999

    def enviar_imagen(self, id_imagen: int, ruta: str, transformaciones) -> str:
        """
        Serializa las transformaciones como JSON string antes de llamar a Pyro5
        para evitar el error 'unhashable type: dict' con el serializador serpent.
        """
        if transformaciones and isinstance(transformaciones[0], str):
            transfs_norm = [{"tipo": t, "parametros": {}, "orden": i}
                            for i, t in enumerate(transformaciones)]
        else:
            transfs_norm = list(transformaciones)

        transfs_json = json.dumps(transfs_norm)
        with self.get_proxy() as proxy:
            return proxy.procesar_imagen(id_imagen, ruta, transfs_json)

    def __str__(self):
        return f"Nodo {self.id} ({self.identificador}) carga={self.carga}"