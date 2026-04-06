class Monitor:

    def obtener_estado_nodos(self, nodos):
        return [
            {
                "id": n.id,
                "carga": n.carga,
                "activo": n.activo
            }
            for n in nodos
        ]