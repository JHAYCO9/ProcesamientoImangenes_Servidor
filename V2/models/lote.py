class Lote:

    def __init__(self, id_lote, nombres, datos, transfs):
        self.id = id_lote
        self.nombres = nombres
        self.datos = datos
        self.transfs = transfs
        self.estado = "PENDIENTE"