import socket
import threading
import json

HOST = "127.0.0.1"
PUERTO = 5002

workers = {}
bloqueo = threading.Lock()
ejecutando = True


def enviar(conexion, mensaje):
    datos = json.dumps(mensaje) + "\n"
    conexion.sendall(datos.encode("utf-8"))


def atender_worker(conexion, direccion):
    nombre = None

    try:
        lector = conexion.makefile("r", encoding="utf-8")

        for linea in lector:
            mensaje = json.loads(linea)
            tipo = mensaje.get("tipo")

            if tipo == "registro":
                nuevo_nombre = mensaje.get("nombre")

                if not nuevo_nombre:
                    break

                with bloqueo:
                    if nuevo_nombre in workers:
                        enviar(conexion, {
                            "tipo": "error",
                            "datos": "Nombre ya registrado"
                        })
                        break

                    nombre = nuevo_nombre
                    workers[nombre] = conexion

                print(f"\n{nombre} conectado desde {direccion}")
                enviar(conexion, {
                    "tipo": "confirmacion",
                    "datos": "Registro correcto"
                })

            elif tipo == "resultado":
                print(f"\nResultado de {nombre}: {mensaje.get('datos')}")

    except (OSError, ValueError, KeyError) as error:
        print(f"\nError de conexion: {error}")

    finally:
        with bloqueo:
            if nombre and workers.get(nombre) is conexion:
                del workers[nombre]
        conexion.close()
        print(f"\nWorker desconectado: {nombre}")


def aceptar_workers(servidor):
    while ejecutando:
        try:
            conexion, direccion = servidor.accept()
            hilo = threading.Thread(
                target=atender_worker,
                args=(conexion, direccion),
                daemon=True
            )
            hilo.start()
        except OSError:
            break


def iniciar_servidor():
    global ejecutando

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        servidor.bind((HOST, PUERTO))
        servidor.listen()
        print(f"Master TCP escuchando en {HOST}:{PUERTO}")

        hilo = threading.Thread(
            target=aceptar_workers,
            args=(servidor,),
            daemon=True
        )
        hilo.start()

        while True:
            print("\n1. Ver Workers")
            print("2. Enviar comando")
            print("3. Salir")
            opcion = input("Opcion: ")

            if opcion == "1":
                with bloqueo:
                    nombres = list(workers.keys())
                print("Workers conectados:", nombres)

            elif opcion == "2":
                nombre = input("Nombre del Worker: ").strip()
                comando = input(
                    "Comando (STATUS, FETCH_LOGS, EXEC_TASK): "
                ).strip().upper()

                with bloqueo:
                    conexion = workers.get(nombre)

                if conexion:
                    try:
                        enviar(conexion, {
                            "tipo": "comando",
                            "accion": comando
                        })
                        print("Comando enviado")
                    except OSError:
                        print("Error al enviar el comando")
                else:
                    print("Worker no encontrado")

            elif opcion == "3":
                print("Cerrando Master...")
                break
            else:
                print("Opcion incorrecta")

    except OSError as error:
        print("Error del servidor:", error)
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido")
    finally:
        ejecutando = False
        servidor.close()
        with bloqueo:
            conexiones = list(workers.values())
            workers.clear()
        for conexion in conexiones:
            try:
                conexion.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conexion.close()
        print("Servidor cerrado")


if __name__ == "__main__":
    iniciar_servidor()
