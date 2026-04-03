from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from interfaces.i_gestor_bd import IGestorBD
from modelos.base import Base
from modelos.usuario import Usuario
from modelos.solicitud_lote import SolicitudLote
from modelos.imagen import Imagen
from modelos.nodo import Nodo
from modelos.log_ejecucion import LogEjecucion
from comun.enums import EstadoNodo


class GestorBD(IGestorBD):

    def __init__(self, url_bd: str):
        self.url_bd = url_bd
        self.engine = create_engine(url_bd, echo=False)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def crear_tablas(self) -> None:
        Base.metadata.create_all(self.engine)

    def guardar(self, entidad) -> None:
        with self.Session() as session:
            session.add(entidad)
            session.commit()
            session.refresh(entidad)

    def obtener(self, modelo, filtros: dict):
        with self.Session() as session:
            resultados = session.query(modelo).filter_by(**filtros).all()
            session.expunge_all()
            return resultados

    def actualizar(self, modelo, id: int, datos: dict) -> None:
        with self.Session() as session:
            session.query(modelo).filter_by(id=id).update(datos)
            session.commit()

    def eliminar(self, modelo, id: int) -> None:
        with self.Session() as session:
            obj = session.query(modelo).get(id)
            if obj:
                session.delete(obj)
                session.commit()

    def guardar_usuario(self, u: Usuario) -> None:
        with self.Session() as session:
            session.add(u)
            session.commit()
            session.refresh(u)

    def obtener_usuario_por_email(self, email: str):
        with self.Session() as session:
            u = session.query(Usuario).filter_by(email=email).first()
            if u:
                session.expunge(u)
            return u

    def guardar_solicitud_lote(self, s: SolicitudLote) -> None:
        with self.Session() as session:
            session.add(s)
            session.commit()
            session.refresh(s)
            # Forzar carga de imagenes antes de cerrar la sesión
            _ = [img for img in s.imagenes]
            session.expunge_all()

    def actualizar_estado_lote(self, id_lote: int, estado) -> None:
        with self.Session() as session:
            session.query(SolicitudLote).filter_by(id_lote=id_lote).update({"estado": estado})
            session.commit()

    def guardar_imagen(self, img: Imagen) -> None:
        with self.Session() as session:
            session.add(img)
            session.commit()
            session.refresh(img)
            session.expunge(img)

    def actualizar_imagen(self, img: Imagen) -> None:
        with self.Session() as session:
            session.merge(img)
            session.commit()

    def guardar_nodo(self, n: Nodo) -> None:
        with self.Session() as session:
            session.add(n)
            session.commit()
            session.refresh(n)
            session.expunge(n)

    def actualizar_nodo(self, id_nodo: int, estado) -> None:
        with self.Session() as session:
            session.query(Nodo).filter_by(id_nodo=id_nodo).update({"estado": estado})
            session.commit()

    def obtener_nodos_activos(self) -> list:
        with self.Session() as session:
            nodos = session.query(Nodo).filter_by(estado=EstadoNodo.ACTIVO).all()
            session.expunge_all()
            return nodos

    def obtener_imagen_por_id(self, id_imagen: int):
        with self.Session() as session:
            imagen = session.query(Imagen).filter_by(id_imagen=id_imagen).first()
            if imagen:
                session.expunge(imagen)
            return imagen

    def obtener_lote_por_id(self, id_lote: int):
        with self.Session() as session:
            lote = session.query(SolicitudLote).filter_by(id_lote=id_lote).first()
            if lote:
                session.expunge(lote)
            return lote

    def actualizar_lote(self, lote: SolicitudLote) -> None:
        with self.Session() as session:
            session.merge(lote)
            session.commit()

    def guardar_log(self, log: LogEjecucion) -> None:
        with self.Session() as session:
            session.add(log)
            session.commit()

    def obtener_nodo_por_identificador(self, identificador: str):
        with self.Session() as session:
            nodo = session.query(Nodo).filter_by(identificador=identificador).first()
        if nodo:
            session.expunge(nodo)
        return nodo

    def obtener_logs_por_imagen(self, id_imagen: int) -> list:
        with self.Session() as session:
            logs = session.query(LogEjecucion).filter_by(id_imagen=id_imagen).all()
            session.expunge_all()
            return logs

    def obtener_historial_usuario(self, id_usuario: int) -> list:
        with self.Session() as session:
            lotes = session.query(SolicitudLote).filter_by(id_usuario=id_usuario).all()
            session.expunge_all()
            return lotes
            