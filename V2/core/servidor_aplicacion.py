import queue
import uuid

from core.distribuidor import Distribuidor
from infra.cliente_rest import ClienteREST
from models.nodo import Nodo


# Configuración fija de los 3 nodos (misma máquina, puertos distintos)
NODOS_CONFIG = [
    {"id": 1, "identificador": "nodo_1", "direccion": "localhost", "puerto": 9090},
    {"id": 2, "identificador": "nodo_2", "direccion": "localhost", "puerto": 9091},
    {"id": 3, "identificador": "nodo_3", "direccion": "localhost", "puerto": 9092},
]


class ServidorAplicacion:
    _instancia = None

    def __init__(self):
        self.cola_trabajos = queue.Queue()
        self.cliente_bd    = ClienteREST("http://localhost:5000")
        self._lotes_bd = {}   # mapeo uuid → id_lote_bd

        # Registrar los 3 nodos
        self.nodos = []
        for cfg in NODOS_CONFIG:
            nodo = Nodo(cfg["id"], cfg["identificador"], cfg["direccion"], cfg["puerto"])
            if nodo.ping():
                self.nodos.append(nodo)
                print(f"[Servidor] ✅ Nodo conectado: {nodo}")
            else:
                print(f"[Servidor] ⚠️ Nodo no disponible: {cfg['identificador']} (puerto {cfg['puerto']})")

        if not self.nodos:
            print("[Servidor] ⚠️ Ningún nodo disponible al iniciar. Se reintentará al despachar.")
            for cfg in NODOS_CONFIG:
                self.nodos.append(Nodo(cfg["id"], cfg["identificador"], cfg["direccion"], cfg["puerto"]))

        self.distribuidor = Distribuidor(self.cola_trabajos, self.nodos, self.cliente_bd)
        self.distribuidor.start()

    @staticmethod
    def get_instancia():
        if ServidorAplicacion._instancia is None:
            ServidorAplicacion._instancia = ServidorAplicacion()
        return ServidorAplicacion._instancia

    # ── Auth ──────────────────────────────────────────────────

    def login(self, email: str, password: str) -> str:
        res = self.cliente_bd.login(email, password)
        print("Respuesta BD login:", res)
        if not res or "token" not in res or not res["token"]:
            print("Login fallido REAL")
            return "ERROR_LOGIN"
        print("Login correcto")
        return res["token"]

    def registrar(self, nombre: str, email: str, password: str) -> str:
        try:
            res = self.cliente_bd.registrar(nombre, email, password)
            return "OK" if res else "ERROR_REGISTRO"
        except Exception:
            return "ERROR_REGISTRO"

    def validar_token(self, token: str) -> bool:
        try:
            res = self.cliente_bd.validar_token(token)
            return res.get("valido", False)
        except Exception:
            return False

    # ── Lotes ─────────────────────────────────────────────────

    def enviar_lote(self, token: str, nombres: list, datos: list,
                   transfs_por_imagen: list) -> dict:
        """
        transfs_por_imagen: lista de listas. Cada elemento corresponde a una imagen
        y contiene sus transformaciones (cada una puede ser str o dict con {tipo, parametros, orden}).
        Compatible también con lista plana de strings (se aplica igual a todas las imágenes).
        """
        if not self.validar_token(token):
            return {"id_lote": "ERROR_TOKEN", "ids_imagenes": []}

        # Normalizar: si recibimos lista plana de strings aplicar a todas las imágenes
        if transfs_por_imagen and not isinstance(transfs_por_imagen[0], list):
            transfs_por_imagen = [transfs_por_imagen for _ in nombres]

        id_lote = str(uuid.uuid4())
        total   = len(nombres)

        # Registrar lote en BD con total_imagenes correcto
        id_lote_bd = self.cliente_bd.crear_lote({
            "token": token,
            "total_imagenes": total
        })

        # Guardar mapeo UUID → id_lote_bd
        self._lotes_bd[id_lote] = id_lote_bd

        # Crear imágenes en BD y obtener sus IDs
        ids_imagenes = []
        for nombre in nombres:
            id_img = self.cliente_bd.crear_imagen(id_lote_bd, nombre)
            ids_imagenes.append(str(id_img))

        lote = {
            "id":               id_lote,
            "token":            token,
            "nombres":          nombres,
            "datos":            datos,
            "transfs_por_imagen": transfs_por_imagen,
            "id_lote_bd":       id_lote_bd,
            "ids_imagenes":     ids_imagenes,
            "estado":           "PENDIENTE"
        }

        self.cola_trabajos.put(lote)
        print(f"📦 Lote encolado: {id_lote} ({total} imágenes) → IDs BD: {ids_imagenes}")
        return {"id_lote": id_lote, "ids_imagenes": ids_imagenes}

    # ── Consultas ─────────────────────────────────────────────

    def consultar_progreso(self, token: str, id_lote: str) -> str:
        if not self.validar_token(token):
            return "ERROR_TOKEN"
        try:
            import requests as req
            id_lote_bd = self._lotes_bd.get(id_lote)
            if not id_lote_bd:
                return "LOTE_NO_ENCONTRADO"
            resp = req.get(f"http://localhost:5000/api/lotes/{id_lote_bd}", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                total     = data.get("total_imagenes", 0)
                completadas = data.get("imagenes_completadas", 0)
                estado    = data.get("estado", "PENDIENTE")
                progreso  = data.get("progreso", 0)
                return f"{estado} ({completadas}/{total}) — {progreso:.1f}%"
        except Exception as e:
            print(f"[Servidor] Error consultando progreso: {e}")
        return "PENDIENTE"

    def estado_nodos(self) -> list:
        return [
            {
                "id":            n.id,
                "identificador": n.identificador,
                "activo":        n.activo,
                "carga":         n.carga
            }
            for n in self.nodos
        ]

    def obtener_historial(self, token: str) -> list:
        if not self.validar_token(token):
            return []
        try:
            import requests as req
            user_id = token.split("_")[1]
            resp = req.get(f"http://localhost:5000/api/usuarios/{user_id}/historial", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"[Servidor] Error historial: {e}")
        return []

    def listar_nodos(self, token: str) -> list:
        if not self.validar_token(token):
            return []
        try:
            import requests as req
            resp = req.get("http://localhost:5000/api/nodos/activos", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"[Servidor] Error listando nodos: {e}")
        return []

    def descargar_lote_zip(self, token: str, id_lote_uuid: str) -> str:
        if not self.validar_token(token):
            return ""
        try:
            import os
            import requests as req
            import base64
            import zipfile
            import io
            id_lote_bd = self._lotes_bd.get(id_lote_uuid)
            if not id_lote_bd:
                return ""
            resp = req.get(f"http://localhost:5000/api/lotes/{id_lote_bd}/imagenes", timeout=5)
            if resp.status_code != 200:
                return ""
            imagenes = resp.json()
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for img in imagenes:
                    resp2 = req.get(f"http://localhost:5000/api/imagenes/{img['id_imagen']}", timeout=5)
                    if resp2.status_code == 200:
                        ruta = resp2.json().get("ruta_resultado")
                        if ruta and os.path.exists(ruta):
                            zf.write(ruta, os.path.basename(ruta))
            return base64.b64encode(zip_buffer.getvalue()).decode("utf-8")
        except Exception as e:
            print(f"[Servidor] Error zip: {e}")
        return ""