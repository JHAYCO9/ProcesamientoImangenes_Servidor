import requests


class ClienteREST:

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    # ── Auth ──────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict:
        r = requests.post(f"{self.base_url}/api/login",
                          json={"email": email, "password": password})
        return r.json()

    def registrar(self, nombre: str, email: str, password: str) -> dict:
        r = requests.post(f"{self.base_url}/api/usuarios",
                          json={"nombre": nombre, "email": email, "password": password})
        return r.json()

    def validar_token(self, token: str) -> dict:
        r = requests.post(f"{self.base_url}/api/validar_token",
                          json={"token": token})
        return r.json()

    # ── Lotes ─────────────────────────────────────────────────

    def crear_lote(self, lote: dict) -> int:
        """
        Registra el lote en la BD y retorna su id numérico.
        lote debe contener: token, total_imagenes.
        """
        try:
            token = lote.get("token", "")
            # Extraer user_id del token (formato TOKEN_<id>)
            user_id = int(token.split("_")[1]) if "_" in token else 1
            total_imagenes = lote.get("total_imagenes", 0)

            r = requests.post(f"{self.base_url}/api/lotes",
                              json={
                                  "id_usuario":     user_id,
                                  "total_imagenes": total_imagenes,
                                  "estado":         "PENDIENTE"
                              })
            data = r.json()
            return data.get("id_lote", 0)
        except Exception as e:
            print(f"[ClienteREST] Error creando lote: {e}")
            return 0

    def actualizar_estado_lote(self, id_lote: int, estado: str) -> None:
        try:
            requests.put(f"{self.base_url}/api/lotes/{id_lote}/estado",
                         json={"estado": estado})
        except Exception as e:
            print(f"[ClienteREST] Error actualizando lote: {e}")

    # ── Imágenes ──────────────────────────────────────────────

    def crear_imagen(self, id_lote: int, nombre: str) -> int:
        try:
            extension = nombre.rsplit('.', 1)[-1].upper() if '.' in nombre else 'PNG'
            r = requests.post(f"{self.base_url}/api/imagenes",
                              json={
                                  "id_lote":          id_lote,
                                  "nombre_archivo":   nombre,
                                  "ruta_original":    f"temp/{nombre}",
                                  "formato_original": extension,
                                  "estado":           "PENDIENTE"
                              })
            if not r.text.strip():
                print(f"[ClienteREST] Respuesta vacía al crear imagen")
                return 0
            data = r.json()
            return data.get("id_imagen", 0)
        except Exception as e:
            print(f"[ClienteREST] Error creando imagen: {e}")
            return 0

    # ── Nodos ─────────────────────────────────────────────────

    def obtener_nodos_activos(self) -> list:
        try:
            r = requests.get(f"{self.base_url}/api/nodos/activos")
            return r.json()
        except Exception:
            return []