import requests
import base64
from xml.etree import ElementTree as ET
import zeep

SERVIDOR = "http://localhost:8000/"
TNS = "procesamiento.imagenes"

from xml.sax.saxutils import escape

def _e(text: str) -> str:
    return escape(str(text))

def _llamar(action: str, inner_xml: str) -> ET.Element:
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:tns="{TNS}">'
        "<soapenv:Body>"
        f"<tns:{action}>{inner_xml}</tns:{action}>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )
    resp = requests.post(
        SERVIDOR,
        data=body.encode("utf-8"),
        headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": action},
        timeout=30
    )
    root = ET.fromstring(resp.text)
    # Busca Fault
    for el in root.iter():
        if el.tag.split("}")[-1] == "Fault":
            fs = next((c for c in el if c.tag.split("}")[-1] == "faultstring"), None)
            raise Exception(fs.text if fs is not None else "Error SOAP")
    return root


def _get(root, tag: str) -> str:
    for el in root.iter():
        if el.tag.split("}")[-1] == tag:
            return (el.text or "").strip()
    return ""


def _get_children(root, parent_tag: str) -> list:
    for el in root.iter():
        if el.tag.split("}")[-1] == parent_tag:
            return list(el)
    return []


class ClienteConsola:

    def __init__(self):
        self.usuario       = None
        self.token_sesion  = None
        self.sesion_activa = False
        # Conectar al servidor SOAP
        try:
            self.servicio_soap = zeep.Client("http://localhost:8000/?wsdl")
            print("[Cliente] Conectado al servidor SOAP")
        except Exception as e:
            print(f"[Cliente] Error al conectar: {e}")
            self.servicio_soap = None

    def main(self) -> None:
        print("=== Cliente de Procesamiento de Imágenes ===")
        while True:
            self.mostrar_menu()

    def mostrar_menu(self) -> None:
        print("\n1. Registrar usuario")
        print("2. Iniciar sesión")
        print("3. Enviar lote de imágenes")
        print("4. Consultar progreso de lote")
        print("5. Descargar imagen procesada")
        print("6. Descargar lote ZIP")
        print("7. Ver historial")
        print("8. Listar nodos")
        print("9. Cerrar sesión")
        print("0. Salir")

        opcion = input("\nOpción: ").strip()

        if opcion == "1":
            nombre   = input("Nombre: ").strip()
            email    = input("Email: ").strip()
            password = input("Password: ").strip()
            self.registrar(nombre, email, password)

        elif opcion == "2":
            email    = input("Email: ").strip()
            password = input("Password: ").strip()
            self.autenticar(email, password)

        elif opcion == "3":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            rutas_raw = input("Rutas de imágenes (separadas por coma): ").strip()
            transfs   = input("Transformaciones (separadas por coma): ").strip()
            rutas         = [r.strip() for r in rutas_raw.split(",")]
            transfs_lista = [t.strip() for t in transfs.split(",")]
            self.enviar_lote(rutas, transfs_lista)

        elif opcion == "4":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            id_lote = int(input("ID del lote: ").strip())
            self.consultar_progreso(id_lote)

        elif opcion == "5":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            id_imagen = int(input("ID de la imagen: ").strip())
            self.descargar_imagen(id_imagen)

        elif opcion == "6":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            id_lote = int(input("ID del lote: ").strip())
            self.descargar_lote_zip(id_lote)

        elif opcion == "7":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            self.ver_historial()

        elif opcion == "8":
            if not self.sesion_activa:
                print("Debes iniciar sesión primero.")
                return
            self.listar_nodos()

        elif opcion == "9":
            self.cerrar_sesion()

        elif opcion == "0":
            print("Saliendo...")
            exit(0)

        else:
            print("Opción no válida.")

    # ─── Operaciones ────────────────────────────────────────────────────────────

    def autenticar(self, email: str, password: str) -> None:
        try:
            root = _llamar("login", f"<email>{email}</email><password>{password}</password>")
            self.token_sesion  = _get(root, "token")
            self.sesion_activa = True
            print(f"Sesión iniciada. Token: {self.token_sesion[:8]}...")
        except Exception as e:
            print(f"Error al autenticar: {e}")

    def registrar(self, nombre: str, email: str, password: str) -> None:
        try:
            root      = _llamar("registrar", f"<nombre>{nombre}</nombre><email>{email}</email><password>{password}</password>")
            resultado = _get(root, "resultado")
            print("Registrado correctamente." if resultado == "OK" else "Error al registrar.")
        except Exception as e:
            print(f"Error al registrar: {e}")

    def cerrar_sesion(self) -> None:
        self.token_sesion  = None
        self.sesion_activa = False
        print("Sesión cerrada.")

    def enviar_lote(self, rutas: list, transfs: list) -> None:
        try:
            # Construir XML con las rutas completas
            nombres_xml = "".join(f"<item>{_e(r)}</item>" for r in rutas)
            transfs_xml = "".join(f"<item>{_e(t)}</item>" for t in transfs)
        
            inner = (
                f"<token>{_e(self.token_sesion)}</token>"
                f"<nombres>{nombres_xml}</nombres>"
                f"<datos></datos>"  # Vacío por ahora
                f"<transfs>{transfs_xml}</transfs>"
            )
        
            root = _llamar("enviarLote", inner)
            id_lote = _get(root, "id_lote")
            print(f"Lote enviado. ID: {id_lote}")
        except Exception as e:
            print(f"Error al enviar lote: {e}")

    def consultar_progreso(self, id_lote: int) -> None:
        try:
            inner    = f"<token>{self.token_sesion}</token><id_lote>{id_lote}</id_lote>"
            root     = _llamar("consultarProgreso", inner)
            estado   = _get(root, "estado")
            progreso = float(_get(root, "progreso") or 0)
            print(f"Estado: {estado} — Progreso: {progreso:.1f}%")
        except Exception as e:
            print(f"Error al consultar progreso: {e}")

    def descargar_imagen(self, id_imagen: int) -> None:
        try:
            inner  = f"<token>{self.token_sesion}</token><id_imagen>{id_imagen}</id_imagen>"
            root   = _llamar("descargarImagen", inner)
            b64    = _get(root, "datos")
            datos  = base64.b64decode(b64)
            nombre = f"imagen_{id_imagen}.jpg"
            with open(nombre, "wb") as f:
                f.write(datos)
            print(f"Imagen guardada como {nombre}")
        except Exception as e:
            print(f"Error al descargar imagen: {e}")

    def descargar_lote_zip(self, id_lote: int) -> None:
        try:
            inner  = f"<token>{self.token_sesion}</token><id_lote>{id_lote}</id_lote>"
            root   = _llamar("descargarLoteZip", inner)
            b64    = _get(root, "datos")
            datos  = base64.b64decode(b64)
            nombre = f"lote_{id_lote}.zip"
            with open(nombre, "wb") as f:
                f.write(datos)
            print(f"Lote guardado como {nombre}")
        except Exception as e:
            print(f"Error al descargar lote: {e}")

    def ver_historial(self) -> None:
        try:
            root  = _llamar("obtenerHistorial", f"<token>{self.token_sesion}</token>")
            lotes = _get_children(root, "historial")
            if not lotes:
                print("Sin historial.")
                return
            print("\n--- Historial ---")
            for lote in lotes:
                children = {c.tag.split("}")[-1]: (c.text or "") for c in lote}
                print(f"  Lote {children.get('id_lote')} — {children.get('estado')} — {children.get('fecha')}")
        except Exception as e:
            print(f"Error al obtener historial: {e}")

    def listar_nodos(self) -> None:
        try:
            root  = _llamar("listarNodos", f"<token>{self.token_sesion}</token>")
            nodos = _get_children(root, "nodos")
            if not nodos:
                print("Sin nodos registrados.")
                return
            print("\n--- Nodos activos ---")
            for nodo in nodos:
                children = {c.tag.split("}")[-1]: (c.text or "") for c in nodo}
                print(f"  Nodo {children.get('id')} — {children.get('identificador')} — {children.get('estado')}")
        except Exception as e:
            print(f"Error al listar nodos: {e}")


if __name__ == "__main__":
    cliente = ClienteConsola()
    cliente.main()