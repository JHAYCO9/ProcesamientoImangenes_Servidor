import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor


class Distribuidor(threading.Thread):
    """
    Consume la cola de lotes, descompone cada lote en imágenes
    y envía cada imagen al nodo con menos carga activa.
    Usa un ThreadPoolExecutor para despachar en paralelo.
    """

    INTERVALO_POLL  = 0.5   # segundos entre checks de la cola
    INTERVALO_RETRY = 3     # segundos de espera si no hay nodos disponibles

    def __init__(self, cola, nodos, cliente_bd, max_workers: int = 10):
        super().__init__(daemon=True)
        self.cola       = cola
        self.nodos      = nodos
        self.cliente_bd = cliente_bd
        self.executor   = ThreadPoolExecutor(max_workers=max_workers)

    def run(self):
        print("[Distribuidor] Iniciado, esperando trabajos...")
        while True:
            try:
                if not self.cola.empty():
                    lote = self.cola.get()
                    self._despachar_lote(lote)
            except Exception as e:
                print(f"[Distribuidor] Error en loop: {e}")
            time.sleep(self.INTERVALO_POLL)

    # ── Lógica de despacho ────────────────────────────────────

    def _despachar_lote(self, lote: dict):
        print(f"[Distribuidor] Procesando lote {lote['id']} — {len(lote['nombres'])} imágenes")

        ids_imagenes     = lote.get("ids_imagenes", [])
        transfs_por_img  = lote.get("transfs_por_imagen", [])
        id_lote_bd       = lote.get("id_lote_bd", 0)
        total            = len(ids_imagenes)

        # Actualizar lote a EN_PROCESO
        try:
            self.cliente_bd.actualizar_estado_lote(id_lote_bd, "EN_PROCESO")
        except Exception as e:
            print(f"[Distribuidor] Error actualizando lote a EN_PROCESO: {e}")

        # Lanzar una tarea por imagen
        futures = []
        for idx, (nombre, datos, transfs, id_imagen) in enumerate(
            zip(lote["nombres"], lote["datos"], transfs_por_img, ids_imagenes)
        ):
            id_imagen = int(id_imagen)
            ruta      = self._guardar_temp(id_imagen, nombre, datos)
            f = self.executor.submit(
                self._enviar_a_nodo, id_imagen, ruta, transfs, id_lote_bd, idx
            )
            futures.append(f)

        # Monitorear en background para actualizar estado del lote al finalizar
        self.executor.submit(self._monitorear_lote, id_lote_bd, futures, total)

    def _monitorear_lote(self, id_lote_bd: int, futures: list, total: int):
        """Espera a que todas las imágenes terminen y actualiza estado del lote."""
        errores = 0
        for f in futures:
            try:
                f.result()
            except Exception:
                errores += 1
        estado_final = "COMPLETADO" if errores == 0 else ("ERROR" if errores == total else "COMPLETADO")
        try:
            self.cliente_bd.actualizar_estado_lote(id_lote_bd, estado_final)
            print(f"[Distribuidor] Lote {id_lote_bd} → {estado_final} ({errores} errores de {total})")
        except Exception as e:
            print(f"[Distribuidor] Error actualizando estado final lote: {e}")

    def _enviar_a_nodo(self, id_imagen: int, ruta: str,
                       transformaciones, id_lote: int, idx: int):
        nodo = self._seleccionar_nodo()
        if not nodo:
            print(f"[Distribuidor] ⚠️ Sin nodos disponibles para imagen {id_imagen}")
            return

        try:
            print(f"[Distribuidor] → Imagen {id_imagen} → {nodo}")
            nodo.carga += 1
            # Normalizar transformaciones a lista de strings o dicts según lo acepta el nodo
            if transformaciones and isinstance(transformaciones[0], dict):
                # Pasar dicts con tipo/parametros/orden
                nodo.enviar_imagen(id_imagen, ruta, transformaciones)
            else:
                nodo.enviar_imagen(id_imagen, ruta, transformaciones)
            print(f"[Distribuidor] ✅ Imagen {id_imagen} completada en {nodo.identificador}")
        except Exception as e:
            print(f"[Distribuidor] ❌ Error enviando imagen {id_imagen} a {nodo}: {e}")
            nodo.activo = False
            raise   # re-lanzar para que _monitorear_lote lo contabilice
        finally:
            nodo.carga = max(0, nodo.carga - 1)

    def _seleccionar_nodo(self):
        """Elige el nodo activo con menor carga. Reintenta si no hay ninguno."""
        for _ in range(5):
            disponibles = [n for n in self.nodos if n.disponible()]
            if disponibles:
                return min(disponibles, key=lambda n: n.get_carga())
            print("[Distribuidor] Sin nodos disponibles, reintentando...")
            time.sleep(self.INTERVALO_RETRY)
        return None

    def _guardar_temp(self, id_imagen: int, nombre: str, datos: bytes) -> str:
        """Guarda los bytes de la imagen en un directorio temporal del servidor."""
        directorio = "temp_imagenes"
        os.makedirs(directorio, exist_ok=True)
        ruta = os.path.join(directorio, f"{id_imagen}_{nombre}")
        with open(ruta, "wb") as f:
            f.write(datos)
        return os.path.abspath(ruta)