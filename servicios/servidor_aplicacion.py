import Pyro5.api
import Pyro5.server
import threading
import queue
import time
from interfaces.i_gestor_bd import IGestorBD
from modelos.nodo import Nodo
from modelos.solicitud_lote import SolicitudLote
from comun.enums import EstadoNodo, EstadoLote


class ServidorAplicacion:
    _instancia = None
    _lock = threading.Lock()

    def __new__(cls, gestor_bd: IGestorBD = None):
        with cls._lock:
            if cls._instancia is None:
                cls._instancia = super().__new__(cls)
                cls._instancia._inicializado = False
        return cls._instancia

    @classmethod
    def get_instancia(cls):
        return cls._instancia

    def __init__(self, gestor_bd: IGestorBD = None):
        if self._inicializado:
            return
        self.cola_trabajos     = queue.Queue()
        self.nodos_registrados = []
        self.gestor_bd         = gestor_bd
        self.hilo_distribuidor = None
        self.hilo_monitor      = None
        self._corriendo        = False
        self._inicializado     = True

    def iniciar(self, host: str, puerto: int) -> None:
        self._corriendo = True
        self.hilo_distribuidor = threading.Thread(
            target=self._loop_distribuidor, daemon=True, name="distribuidor"
        )
        self.hilo_monitor = threading.Thread(
            target=self._loop_monitor, daemon=True, name="monitor"
        )
        self.hilo_distribuidor.start()
        self.hilo_monitor.start()
        print(f"[Servidor] Iniciado en {host}:{puerto}")

    def detener(self) -> None:
        self._corriendo = False
        print("[Servidor] Detenido.")

    def recibir_solicitud_lote(self, s: SolicitudLote) -> None:
        self.gestor_bd.guardar_solicitud_lote(s)
        self.cola_trabajos.put(s)

    def _loop_distribuidor(self) -> None:
        while self._corriendo:
            try:
                solicitud = self.cola_trabajos.get(timeout=1)
                self.distribuir_trabajos(solicitud)
            except queue.Empty:
                continue

    def distribuir_trabajos(self, solicitud: SolicitudLote) -> None:
        nodo = self.seleccionar_nodo()
        if nodo is None:
            print("[Servidor] Sin nodos disponibles, reintentando...")
            self.cola_trabajos.put(solicitud)
            time.sleep(2)
            return
        try:
            proxy = nodo.get_proxy_pyro5()
            for imagen in solicitud.get_imagenes():
                # Enviar directamente la lista de strings
                transformaciones = imagen.transformaciones_pendientes  # Esto ya es ["GRISES", "ROTAR"]
                print(f"[Servidor] Enviando transformaciones: {transformaciones}")
            
            proxy.procesar_imagen(
                imagen.id_imagen,
                imagen.ruta_original,
                transformaciones  # ← Lista de strings, no diccionarios
            )
            nodo.incrementar_trabajo()
        except Exception as e:
            print(f"[Servidor] Error en nodo {nodo.identificador}: {e}")
            nodo.estado = EstadoNodo.ERROR
            self.gestor_bd.actualizar_nodo(nodo.id_nodo, EstadoNodo.ERROR)

    def seleccionar_nodo(self):
        disponibles = [n for n in self.nodos_registrados if n.esta_disponible()]
        if not disponibles:
            return None
        return min(disponibles, key=lambda n: n.trabajos_activos)

    def registrar_nodo(self, nodo: Nodo) -> None:
        self.nodos_registrados.append(nodo)
        self.gestor_bd.guardar_nodo(nodo)
        print(f"[Servidor] Nodo registrado: {nodo.identificador}")

    def _loop_monitor(self) -> None:
        while self._corriendo:
            self.verificar_estado_nodos()
            time.sleep(10)

    def verificar_estado_nodos(self) -> None:
        for nodo in self.nodos_registrados:
            try:
                proxy = nodo.get_proxy_pyro5()
                proxy.ping()
                if nodo.estado != EstadoNodo.ACTIVO:
                    nodo.estado = EstadoNodo.ACTIVO
                    self.gestor_bd.actualizar_nodo(nodo.id_nodo, EstadoNodo.ACTIVO)
            except Exception:
                nodo.estado = EstadoNodo.ERROR
                self.gestor_bd.actualizar_nodo(nodo.id_nodo, EstadoNodo.ERROR)
                print(f"[Monitor] Nodo caído: {nodo.identificador}")
    
    @Pyro5.server.expose
    def imagen_completada(self, id_imagen: int) -> None:
        """Recibe notificación del nodo cuando una imagen termina"""
        try:
            # Obtener la imagen y su lote
            imagen = self.gestor_bd.obtener_imagen_por_id(id_imagen)
            if imagen:
                lote = self.gestor_bd.obtener_lote_por_id(imagen.id_lote)
            if lote:
                lote.imagenes_completadas += 1
                print(f"[Servidor] Progreso lote {lote.id_lote}: {lote.imagenes_completadas}/{lote.total_imagenes}")
                
                if lote.imagenes_completadas == lote.total_imagenes:
                    lote.estado = EstadoLote.COMPLETADO
                    print(f"[Servidor] Lote {lote.id_lote} completado!")
                
                self.gestor_bd.actualizar_lote(lote)
        except Exception as e:
            print(f"[Servidor] Error al procesar notificación: {e}")