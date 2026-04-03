import secrets
import zipfile
import io
from interfaces.i_servicio_imagenes import IServicioImagenes
from servicios.servidor_aplicacion import ServidorAplicacion
from modelos.usuario import Usuario
from modelos.solicitud_lote import SolicitudLote
from modelos.imagen import Imagen

class InterfazSoap(IServicioImagenes):

    def __init__(self, gestor_bd, servidor: ServidorAplicacion):
        self.gestor_bd = gestor_bd
        self.servidor  = servidor
        self._sesiones = {}  # token -> id_usuario

    def _validar_token(self, token: str) -> int:
        id_usuario = self._sesiones.get(token)
        if id_usuario is None:
            raise PermissionError("Token inválido o sesión expirada")
        return id_usuario

    def login(self, email: str, password: str) -> str:
        usuario = self.gestor_bd.obtener_usuario_por_email(email)
        if usuario is None or not usuario.verificar_password(password):
            raise ValueError("Credenciales incorrectas")
        token = secrets.token_hex(32)
        self._sesiones[token] = usuario.id_usuario
        return token

    def registrar(self, nombre: str, email: str, password: str) -> bool:
        if self.gestor_bd.obtener_usuario_por_email(email):
            raise ValueError("El email ya está registrado")
        usuario = Usuario()
        usuario.nombre = nombre
        usuario.email  = email
        usuario.set_password(password)
        self.gestor_bd.guardar_usuario(usuario)
        return True

    def enviar_lote(self, token: str, nombres: list, datos: list, transfs: list) -> str:
        id_usuario = self._validar_token(token)
        lote = SolicitudLote()
        lote.id_usuario = id_usuario
    
    # nombres ahora contiene las rutas COMPLETAS
        for i, ruta in enumerate(nombres):
            img = Imagen()
            nombre_archivo = ruta.split("\\")[-1].split("/")[-1]
            img.nombre_archivo = nombre_archivo
            img.ruta_original = ruta  # Usa directamente la ruta
            img.formato_original = nombre_archivo.split(".")[-1] if "." in nombre_archivo else "png"
            img.transformaciones_pendientes = transfs
            lote.agregar_imagen(img)
    
        self.servidor.recibir_solicitud_lote(lote)
        return str(lote.id_lote)

    def consultar_progreso(self, token: str, id_lote: int) -> dict:
        self._validar_token(token)
        resultados = self.gestor_bd.obtener(SolicitudLote, {"id_lote": id_lote})
        if not resultados:
            raise ValueError("Lote no encontrado")
        lote = resultados[0]
        return {
            "id_lote":  lote.id_lote,
            "estado":   lote.estado.value,
            "progreso": lote.get_progreso()
        }

    def descargar_imagen(self, token: str, id_imagen: int) -> bytes:
        self._validar_token(token)
        resultados = self.gestor_bd.obtener(Imagen, {"id_imagen": id_imagen})
        if not resultados:
            raise ValueError("Imagen no encontrada")
        with open(resultados[0].ruta_resultado, "rb") as f:
            return f.read()

    def descargar_lote_zip(self, token: str, id_lote: int) -> bytes:
        self._validar_token(token)
        imagenes = self.gestor_bd.obtener(Imagen, {"id_lote": id_lote})
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            for img in imagenes:
                if img.ruta_resultado:
                    zf.write(img.ruta_resultado, img.nombre_archivo)
        return buffer.getvalue()

    def obtener_historial(self, token: str) -> list:
        id_usuario = self._validar_token(token)
        lotes = self.gestor_bd.obtener_historial_usuario(id_usuario)
        return [
            {"id_lote": l.id_lote, "estado": l.estado.value, "fecha": str(l.fecha_recepcion)}
            for l in lotes
        ]

    def listar_nodos(self, token: str) -> list:
        self._validar_token(token)
        nodos = self.gestor_bd.obtener_nodos_activos()
        return [
            {"id": n.id_nodo, "identificador": n.identificador, "estado": n.estado.value}
            for n in nodos
        ]
