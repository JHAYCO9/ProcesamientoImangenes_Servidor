import Pyro5.api

try:
    proxy = Pyro5.api.Proxy("PYRO:nodo_procesador@localhost:9090")
    
    # Prueba ping
    resultado = proxy.ping()
    print("Ping al nodo:", resultado)
    
    # Prueba estado
    estado = proxy.get_estado()
    print("Estado del nodo:", estado)
    
    # Prueba trabajos pendientes
    trabajos = proxy.get_trabajos_pendientes()
    print("Trabajos pendientes:", trabajos)

except Exception as e:
    print("Error conectando al nodo:", e)