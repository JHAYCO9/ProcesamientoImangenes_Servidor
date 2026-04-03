from config import URL_BD, HOST, PUERTO_SOAP
from repositorio.gestor_bd import GestorBD
from servicios.servidor_aplicacion import ServidorAplicacion
from servicios.interfaz_soap import InterfazSoap
from servicios.soap_server import crear_soap_server
from modelos.nodo import Nodo
from comun.enums import EstadoNodo
import time
import threading
import Pyro5.api


def main():
    # 1. Base de datos
    gestor_bd = GestorBD(URL_BD)
    gestor_bd.crear_tablas()

    # 2. Lógica de negocio
    servidor = ServidorAplicacion(gestor_bd)
    servidor.iniciar(HOST, PUERTO_SOAP)

    # 3. Registrar nodo local para pruebas
    from sqlalchemy.orm import sessionmaker
    with sessionmaker(bind=gestor_bd.engine, expire_on_commit=False)() as session:
        nodo = session.query(Nodo).filter_by(identificador="nodo_1").first()
        if nodo is None:
            nodo = Nodo()
            nodo.identificador  = "nodo_1"
            nodo.direccion_red  = "localhost"
            nodo.puerto_pyro5   = 9090
            nodo.estado         = EstadoNodo.ACTIVO
            nodo.trabajos_activos = 0
            session.add(nodo)
            session.commit()
        session.expunge(nodo)
    servidor.nodos_registrados.append(nodo)
    print(f"[Servidor] Nodo registrado: {nodo.identificador}")

    # 4. Capa de servicio
    servicio = InterfazSoap(gestor_bd, servidor)

    # 5. Servidor SOAP
    soap = crear_soap_server(servicio, HOST, PUERTO_SOAP)

    # 6. Exponer el servidor via Pyro5 para que el nodo pueda notificar progreso
    pyro5_daemon = Pyro5.api.Daemon(host="localhost", port=9091)
    pyro5_uri = pyro5_daemon.register(servidor, objectId="servidor_aplicacion")
    print(f"[Servidor Pyro5] Expuesto en {pyro5_uri}")
    
    # Hilo para el servidor Pyro5
    pyro5_thread = threading.Thread(target=pyro5_daemon.requestLoop, daemon=True)
    pyro5_thread.start()

    try:
        print("[main] Servidor corriendo. Presiona Ctrl+C para detener.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[main] Apagando servidores...")
        servidor.detener()
        soap.shutdown()
        pyro5_daemon.shutdown()
        print("[main] Apagado completo.")


if __name__ == "__main__":
    main()