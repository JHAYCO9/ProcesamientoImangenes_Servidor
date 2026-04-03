import threading
import base64
from wsgiref.simple_server import make_server, WSGIRequestHandler
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as _e
from servicios.interfaz_soap import InterfazSoap

_servicio: InterfazSoap = None

TNS = "procesamiento.imagenes"


# ─── Silencia logs de wsgiref ────────────────────────────────────────────────
class SilentHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


# ─── WSDL ────────────────────────────────────────────────────────────────────
WSDL = """<?xml version="1.0" encoding="UTF-8"?>
<definitions name="ServicioImagenes"
  targetNamespace="procesamiento.imagenes"
  xmlns="http://schemas.xmlsoap.org/wsdl/"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:tns="procesamiento.imagenes"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">

  <types>
    <xsd:schema targetNamespace="procesamiento.imagenes">
      <xsd:complexType name="StringList">
        <xsd:sequence>
          <xsd:element name="item" type="xsd:string" minOccurs="0" maxOccurs="unbounded"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="LoteInfo">
        <xsd:sequence>
          <xsd:element name="id_lote"  type="xsd:int"/>
          <xsd:element name="estado"   type="xsd:string"/>
          <xsd:element name="fecha"    type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="HistorialList">
        <xsd:sequence>
          <xsd:element name="lote" type="tns:LoteInfo" minOccurs="0" maxOccurs="unbounded"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="NodoInfo">
        <xsd:sequence>
          <xsd:element name="id"            type="xsd:int"/>
          <xsd:element name="identificador" type="xsd:string"/>
          <xsd:element name="estado"        type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="NodoList">
        <xsd:sequence>
          <xsd:element name="nodo" type="tns:NodoInfo" minOccurs="0" maxOccurs="unbounded"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </types>

  <message name="loginRequest">
    <part name="email"    type="xsd:string"/>
    <part name="password" type="xsd:string"/>
  </message>
  <message name="loginResponse"><part name="token" type="xsd:string"/></message>

  <message name="registrarRequest">
    <part name="nombre"   type="xsd:string"/>
    <part name="email"    type="xsd:string"/>
    <part name="password" type="xsd:string"/>
  </message>
  <message name="registrarResponse"><part name="resultado" type="xsd:string"/></message>

  <message name="enviarLoteRequest">
    <part name="token"   type="xsd:string"/>
    <part name="nombres" type="tns:StringList"/>
    <part name="transfs" type="tns:StringList"/>
  </message>
  <message name="enviarLoteResponse"><part name="id_lote" type="xsd:string"/></message>

  <message name="consultarProgresoRequest">
    <part name="token"   type="xsd:string"/>
    <part name="id_lote" type="xsd:int"/>
  </message>
  <message name="consultarProgresoResponse">
    <part name="estado"   type="xsd:string"/>
    <part name="progreso" type="xsd:string"/>
  </message>

  <message name="descargarImagenRequest">
    <part name="token"     type="xsd:string"/>
    <part name="id_imagen" type="xsd:int"/>
  </message>
  <message name="descargarImagenResponse"><part name="datos" type="xsd:base64Binary"/></message>

  <message name="descargarLoteZipRequest">
    <part name="token"   type="xsd:string"/>
    <part name="id_lote" type="xsd:int"/>
  </message>
  <message name="descargarLoteZipResponse"><part name="datos" type="xsd:base64Binary"/></message>

  <message name="obtenerHistorialRequest"><part name="token" type="xsd:string"/></message>
  <message name="obtenerHistorialResponse"><part name="historial" type="tns:HistorialList"/></message>

  <message name="listarNodosRequest"><part name="token" type="xsd:string"/></message>
  <message name="listarNodosResponse"><part name="nodos" type="tns:NodoList"/></message>

  <portType name="ServicioImagenesPort">
    <operation name="login">
      <input message="tns:loginRequest"/><output message="tns:loginResponse"/>
    </operation>
    <operation name="registrar">
      <input message="tns:registrarRequest"/><output message="tns:registrarResponse"/>
    </operation>
    <operation name="enviarLote">
      <input message="tns:enviarLoteRequest"/><output message="tns:enviarLoteResponse"/>
    </operation>
    <operation name="consultarProgreso">
      <input message="tns:consultarProgresoRequest"/><output message="tns:consultarProgresoResponse"/>
    </operation>
    <operation name="descargarImagen">
      <input message="tns:descargarImagenRequest"/><output message="tns:descargarImagenResponse"/>
    </operation>
    <operation name="descargarLoteZip">
      <input message="tns:descargarLoteZipRequest"/><output message="tns:descargarLoteZipResponse"/>
    </operation>
    <operation name="obtenerHistorial">
      <input message="tns:obtenerHistorialRequest"/><output message="tns:obtenerHistorialResponse"/>
    </operation>
    <operation name="listarNodos">
      <input message="tns:listarNodosRequest"/><output message="tns:listarNodosResponse"/>
    </operation>
  </portType>

  <binding name="ServicioImagenesBinding" type="tns:ServicioImagenesPort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="login">
      <soap:operation soapAction="login"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="registrar">
      <soap:operation soapAction="registrar"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="enviarLote">
      <soap:operation soapAction="enviarLote"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="consultarProgreso">
      <soap:operation soapAction="consultarProgreso"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="descargarImagen">
      <soap:operation soapAction="descargarImagen"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="descargarLoteZip">
      <soap:operation soapAction="descargarLoteZip"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="obtenerHistorial">
      <soap:operation soapAction="obtenerHistorial"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
    <operation name="listarNodos">
      <soap:operation soapAction="listarNodos"/>
      <input><soap:body use="literal"/></input>
      <output><soap:body use="literal"/></output>
    </operation>
  </binding>

  <service name="ServicioImagenes">
    <port name="ServicioImagenesPort" binding="tns:ServicioImagenesBinding">
      <soap:address location="http://localhost:8000/"/>
    </port>
  </service>
</definitions>"""


# ─── Helpers XML ─────────────────────────────────────────────────────────────
def _soap_ok(tag: str, inner: str) -> bytes:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        f' xmlns:tns="{TNS}">'
        "<soapenv:Body>"
        f"<tns:{tag}Response>{inner}</tns:{tag}Response>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )
    return xml.encode("utf-8")


def _soap_fault(msg: str) -> bytes:
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soapenv:Body><soapenv:Fault>"
        f"<faultcode>soapenv:Server</faultcode><faultstring>{msg}</faultstring>"
        "</soapenv:Fault></soapenv:Body></soapenv:Envelope>"
    )
    return xml.encode("utf-8")


def _get(root, tag: str) -> str:
    for el in root.iter():
        if el.tag.split("}")[-1] == tag:
            return (el.text or "").strip()
    return ""


def _get_list(root, parent_tag: str) -> list:
    for el in root.iter():
        if el.tag.split("}")[-1] == parent_tag:
            return [(child.text or "").strip() for child in el]
    return []


# ─── Dispatcher ──────────────────────────────────────────────────────────────
def _dispatch(action: str, root) -> bytes:
    try:
        if action == "login":
            token = _servicio.login(_get(root, "email"), _get(root, "password"))
            return _soap_ok("login", f"<token>{_e(token)}</token>")

        elif action == "registrar":
            ok = _servicio.registrar(
                _get(root, "nombre"), _get(root, "email"), _get(root, "password")
            )
            return _soap_ok("registrar", f"<resultado>{'OK' if ok else 'ERROR'}</resultado>")

        elif action == "enviarLote":
            token   = _get(root, "token")
            nombres = _get_list(root, "nombres")
            transfs = _get_list(root, "transfs")
            id_lote = _servicio.enviar_lote(token, nombres, [], transfs)
            return _soap_ok("enviarLote", f"<id_lote>{id_lote}</id_lote>")

        elif action == "consultarProgreso":
            token   = _get(root, "token")
            id_lote = int(_get(root, "id_lote"))
            info    = _servicio.consultar_progreso(token, id_lote)
            return _soap_ok(
                "consultarProgreso",
                f"<estado>{info['estado']}</estado><progreso>{info['progreso']}</progreso>"
            )

        elif action == "descargarImagen":
            token     = _get(root, "token")
            id_imagen = int(_get(root, "id_imagen"))
            datos     = _servicio.descargar_imagen(token, id_imagen)
            b64       = base64.b64encode(datos).decode("utf-8")
            return _soap_ok("descargarImagen", f"<datos>{b64}</datos>")

        elif action == "descargarLoteZip":
            token   = _get(root, "token")
            id_lote = int(_get(root, "id_lote"))
            datos   = _servicio.descargar_lote_zip(token, id_lote)
            b64     = base64.b64encode(datos).decode("utf-8")
            return _soap_ok("descargarLoteZip", f"<datos>{b64}</datos>")

        elif action == "obtenerHistorial":
            token     = _get(root, "token")
            historial = _servicio.obtener_historial(token)
            items = "".join(
                f"<lote><id_lote>{l['id_lote']}</id_lote>"
                f"<estado>{l['estado']}</estado><fecha>{l['fecha']}</fecha></lote>"
                for l in historial
            )
            return _soap_ok("obtenerHistorial", f"<historial>{items}</historial>")

        elif action == "listarNodos":
            token = _get(root, "token")
            nodos = _servicio.listar_nodos(token)
            items = "".join(
                f"<nodo><id>{n['id']}</id>"
                f"<identificador>{n['identificador']}</identificador>"
                f"<estado>{n['estado']}</estado></nodo>"
                for n in nodos
            )
            return _soap_ok("listarNodos", f"<nodos>{items}</nodos>")

        else:
            return _soap_fault(f"Operación desconocida: {action}")

    except PermissionError as e:
        return _soap_fault(_e(str(e)))
    except ValueError as e:
        return _soap_fault(_e(str(e)))
    except Exception as e:
        return _soap_fault(_e(f"Error interno: {str(e)}"))


# ─── WSGI App ─────────────────────────────────────────────────────────────────
def _wsgi_app(environ, start_response):
    method = environ["REQUEST_METHOD"]

    if method == "GET" and "wsdl" in environ.get("QUERY_STRING", "").lower():
        start_response("200 OK", [("Content-Type", "text/xml; charset=utf-8")])
        return [WSDL.encode("utf-8")]

    if method == "POST":
        length = int(environ.get("CONTENT_LENGTH", 0) or 0)
        body   = environ["wsgi.input"].read(length).decode("utf-8")

        soap_action = environ.get("HTTP_SOAPACTION", "").strip('"').split("/")[-1]

        try:
            root = ET.fromstring(body)
        except ET.ParseError as e:
            start_response("400 Bad Request", [("Content-Type", "text/xml; charset=utf-8")])
            return [_soap_fault(f"XML inválido: {e}")]

        if not soap_action:
            ops = ("login", "registrar", "enviarLote", "consultarProgreso",
                   "descargarImagen", "descargarLoteZip", "obtenerHistorial", "listarNodos")
            for el in root.iter():
                local = el.tag.split("}")[-1]
                if local in ops:
                    soap_action = local
                    break

        resp = _dispatch(soap_action, root)
        start_response("200 OK", [("Content-Type", "text/xml; charset=utf-8")])
        return [resp]

    start_response("404 Not Found", [])
    return [b"Not Found"]


# ─── Entry point ─────────────────────────────────────────────────────────────
def crear_soap_server(servicio: InterfazSoap, host: str, puerto: int):
    global _servicio
    _servicio = servicio

    server = make_server(host, puerto, _wsgi_app, handler_class=SilentHandler)

    hilo = threading.Thread(target=server.serve_forever, daemon=True, name="soap-server")
    hilo.start()

    print(f"[SOAP] Servicio expuesto en http://{host}:{puerto}/?wsdl")
    return server