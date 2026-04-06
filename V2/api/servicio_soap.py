import os
import json
import requests
from core.servidor_aplicacion import ServidorAplicacion


class ServicioSOAP:

    def __init__(self):
        self.srv = ServidorAplicacion.get_instancia()

    def _buscar_resultado(self, id_imagen: int) -> str:
        try:
            r = requests.get(f"http://localhost:5000/api/imagenes/{id_imagen}", timeout=5)
            if r.status_code == 200:
                data = r.json()
                ruta = data.get("ruta_resultado")
                return ruta if ruta else None
        except Exception:
            pass
        return None

    def parse_array_string(self, parent):
        return [item.text for item in parent.findall("item")]

    def parse_array_base64(self, parent):
        import base64
        return [base64.b64decode(item.text) for item in parent.findall("item")]

    def parse_transfs_por_imagen(self, parent):
        """
        Parsea el nodo <transfs_por_imagen> del XML.
        Formato esperado: cada <imagen> contiene varios <transf> con <tipo>, <parametros>, <orden>.
        Si el cliente envió el nodo plano <transfs> en su lugar, se acepta como lista uniforme.
        """
        imagenes_node = parent.findall("imagen")
        if imagenes_node:
            resultado = []
            for img_node in imagenes_node:
                transfs_img = []
                for t_node in img_node.findall("transf"):
                    tipo = t_node.findtext("tipo", "")
                    orden = int(t_node.findtext("orden", "0"))
                    params_text = t_node.findtext("parametros", "{}")
                    try:
                        parametros = json.loads(params_text)
                    except Exception:
                        parametros = {}
                    transfs_img.append({"tipo": tipo, "parametros": parametros, "orden": orden})
                resultado.append(transfs_img)
            return resultado
        # Fallback: lista plana de strings (compatibilidad hacia atrás)
        return [item.text for item in parent.findall("item")]

    def procesar_peticion(self, body):

        for child in body:
            metodo = child.tag.split("}")[-1]

            # LOGIN
            if metodo == "login":
                email    = child.find("email").text
                password = child.find("password").text
                token    = self.srv.login(email, password)
                return f"""
                <loginResponse>
                    <return>{token}</return>
                </loginResponse>
                """

            # REGISTRAR
            elif metodo == "registrar":
                nombre   = child.find("nombre").text
                email    = child.find("email").text
                password = child.find("password").text
                res      = self.srv.registrar(nombre, email, password)
                return f"""
                <registrarResponse>
                    <return>{res}</return>
                </registrarResponse>
                """

            # ENVIAR LOTE
            elif metodo == "enviar_lote":
                token   = child.find("token").text
                nombres = self.parse_array_string(child.find("nombres"))
                datos   = self.parse_array_base64(child.find("datos"))

                # Intentar parsear transfs_por_imagen (nodo nuevo) o transfs (nodo antiguo)
                transfs_node = child.find("transfs_por_imagen")
                if transfs_node is not None:
                    transfs_por_imagen = self.parse_transfs_por_imagen(transfs_node)
                else:
                    # Compatibilidad: nodo <transfs> con lista plana aplicada a todas
                    transfs_planas = self.parse_array_string(child.find("transfs"))
                    transfs_por_imagen = [transfs_planas for _ in nombres]

                resultado    = self.srv.enviar_lote(token, nombres, datos, transfs_por_imagen)
                id_lote      = resultado["id_lote"]
                ids_items    = "".join(f"<item>{i}</item>" for i in resultado["ids_imagenes"])

                return f"""
                <enviar_loteResponse>
                    <return>{id_lote}</return>
                    <ids_imagenes>{ids_items}</ids_imagenes>
                </enviar_loteResponse>
                """

            # DESCARGAR IMAGEN
            elif metodo == "descargar_imagen":
                import base64
                token    = child.find("token").text
                id_imagen = int(child.find("id_imagen").text)

                ruta = self._buscar_resultado(id_imagen)
                if ruta and os.path.exists(ruta):
                    with open(ruta, "rb") as f:
                        datos_b64 = base64.b64encode(f.read()).decode("utf-8")
                else:
                    datos_b64 = ""

                return f"""
                <descargar_imagenResponse>
                    <return>{datos_b64}</return>
                </descargar_imagenResponse>
                """

            # HISTORIAL
            elif metodo == "obtener_historial":
                token = child.find("token").text
                res   = self.srv.obtener_historial(token)
                items = "".join(
                    f"<item>"
                    f"<id_lote>{l['id_lote']}</id_lote>"
                    f"<estado>{l['estado']}</estado>"
                    f"<progreso>{l.get('progreso', 0)}</progreso>"
                    f"<total_imagenes>{l.get('total_imagenes', 0)}</total_imagenes>"
                    f"<imagenes_completadas>{l.get('imagenes_completadas', 0)}</imagenes_completadas>"
                    f"</item>"
                    for l in res
                )
                return f"""
                <obtener_historialResponse>
                    <return>{items}</return>
                </obtener_historialResponse>
                """

            # LISTAR NODOS
            elif metodo == "listar_nodos":
                token = child.find("token").text
                res   = self.srv.listar_nodos(token)
                items = "".join(
                    f"<item>"
                    f"<id_nodo>{n['id_nodo']}</id_nodo>"
                    f"<identificador>{n['identificador']}</identificador>"
                    f"<direccion>{n['direccion']}</direccion>"
                    f"<estado>{n.get('estado', 'ACTIVO')}</estado>"
                    f"</item>"
                    for n in res
                )
                return f"""
                <listar_nodosResponse>
                    <return>{items}</return>
                </listar_nodosResponse>
                """

            # DESCARGAR LOTE ZIP
            elif metodo == "descargar_lote_zip":
                token   = child.find("token").text
                id_lote = child.find("id_lote").text
                zip_b64 = self.srv.descargar_lote_zip(token, id_lote)
                return f"""
                <descargar_lote_zipResponse>
                    <return>{zip_b64}</return>
                </descargar_lote_zipResponse>
                """

            # CONSULTAR PROGRESO
            elif metodo == "consultar_progreso":
                token   = child.find("token").text
                id_lote = child.find("id_lote").text
                res     = self.srv.consultar_progreso(token, id_lote)
                return f"""
                <consultar_progresoResponse>
                    <return>{res}</return>
                </consultar_progresoResponse>
                """

        return "<e>Metodo no soportado</e>"