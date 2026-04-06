from http.server import BaseHTTPRequestHandler, HTTPServer
import xml.etree.ElementTree as ET

from api.servicio_soap import ServicioSOAP

soap_service = ServicioSOAP()


class SOAPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/?wsdl":
            with open("wsdl.xml", "rb") as f:
                wsdl = f.read()

            self.send_response(200)
            self.send_header("Content-type", "text/xml")
            self.end_headers()
            self.wfile.write(wsdl)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        request = self.rfile.read(content_length)

        root = ET.fromstring(request)
        body = root.find("{http://schemas.xmlsoap.org/soap/envelope/}Body")

        response_xml = soap_service.procesar_peticion(body)

        soap_response = f"""<?xml version="1.0"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                {response_xml}
            </soap:Body>
        </soap:Envelope>
        """

        self.send_response(200)
        self.send_header("Content-type", "text/xml")
        self.end_headers()
        self.wfile.write(soap_response.encode())


if __name__ == "__main__":
    print("🔥 SOAP Manual corriendo en http://localhost:8000/?wsdl")
    server = HTTPServer(("0.0.0.0", 8000), SOAPHandler)
    server.serve_forever()