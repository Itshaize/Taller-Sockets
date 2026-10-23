"""Servicios TCP y UDP de prueba: escuchan exclusivamente en loopback."""
import socket
import threading

HOST = "127.0.0.1"
TCP_PORT = 9100
UDP_PORT = 9101


def servir_tcp():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, TCP_PORT))
        servidor.listen(30)
        print(f"[OBJETIVO] TCP {HOST}:{TCP_PORT}", flush=True)
        while True:
            conexion, _ = servidor.accept()
            threading.Thread(target=atender_tcp, args=(conexion,), daemon=True).start()


def atender_tcp(conexion):
    with conexion:
        conexion.settimeout(1)
        try:
            if conexion.recv(4) == b"PING":
                conexion.sendall(b"PONG")
        except OSError:
            pass


def servir_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as servidor:
        servidor.bind((HOST, UDP_PORT))
        print(f"[OBJETIVO] UDP {HOST}:{UDP_PORT}", flush=True)
        while True:
            mensaje, origen = servidor.recvfrom(256)
            if mensaje == b"PING":
                servidor.sendto(b"PONG", origen)


if __name__ == "__main__":
    threading.Thread(target=servir_tcp, daemon=True).start()
    servir_udp()
