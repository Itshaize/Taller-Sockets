# Taller de Sockets: UDP y TCP

**Universidad:** Universidad Politecnica Salesiana (UPS)  
**Integrantes:** Mauricio Jacome (MAU), Isma y Dio.

Este repositorio reunira las tres actividades del taller de sockets. Por ahora se incluyen la **Actividad 1: comunicacion UDP** y la **Actividad 2: TCP multihilo**.

## Distribucion del trabajo

- **MAU - Actividad 1 (implementada):** heartbeats UDP, registro de workers, respuesta ACK y deteccion de desconexiones.
- **Isma - Actividad 2 (implementacion inicial en `Actividad2_TCP/`, pendiente de integracion):** servidor TCP multihilo y comunicacion de comandos/resultados.
- **Dio - Actividad 3 (pendiente de integracion):** coordinacion de tareas, carga controlada y reportes.

## Actividad 1: UDP

El worker envia un mensaje cada **2 segundos**. El servidor guarda su identificador, IP, puerto y hora del ultimo heartbeat. Responde con un **ACK**. Si transcurren **6 segundos** sin recibir mensajes, el worker se marca como desconectado. Cuando vuelve a enviar, se registra de nuevo.

**Requisitos:** Ubuntu (u otro Linux) y Python 3. No hay que instalar paquetes externos.

### 1. Descargar desde Ubuntu

```bash
git clone https://github.com/Itshaize/Taller-Sockets.git
cd Taller-Sockets/Actividad1_UDP
```

Para comprobar Python, ejecutar `python3 --version`. Si no esta instalado: `sudo apt update && sudo apt install python3 -y`.

### 2. Iniciar el servidor (Terminal 1)

```bash
python3 servidor_udp.py
```

El servidor usa UDP en el **puerto 5001** y escucha en todas las interfaces (`0.0.0.0`).

### 3. Iniciar dos workers (Terminales 2 y 3)

En cada terminal, entrar primero a `Taller-Sockets/Actividad1_UDP`.

```bash
python3 worker_udp.py worker_01
```

```bash
python3 worker_udp.py worker_02
```

La IP predeterminada del servidor es `127.0.0.1` (la misma computadora). Para probar con otro equipo, consultar la IP del servidor con `hostname -I` y ejecutar en el cliente:

```bash
python3 worker_udp.py worker_03 192.168.1.100
```

Sustituir `192.168.1.100` por la IP real del servidor. Si se utiliza UFW y esta activo, permitir UDP 5001: `sudo ufw allow 5001/udp`.

### 4. Mostrar la desconexion

Detener el `worker_01` con **Ctrl+C**. Aproximadamente **6 segundos despues del ultimo heartbeat**, el servidor mostrara:

```text
[DESCONECTADO] worker_01 (6 s sin heartbeat)
```

El `worker_02` sigue funcionando. Volver a iniciar el primer worker para demostrar el registro nuevamente.

### Mensajes JSON

Heartbeat enviado por el cliente:

```json
{"tipo": "heartbeat", "worker_id": "worker_01"}
```

ACK devuelto por el servidor:

```json
{"tipo": "ack", "worker_id": "worker_01"}
```

**Puertos acordados para la integracion:** UDP `5001` (MAU) y TCP `5002` (propuesta para Isma). La Actividad 1 mantiene el registro en memoria; la integracion con TCP queda pendiente.

## Evidencias para la entrega

1. Captura del servidor registrando dos workers y enviando ACK.
2. Captura de los workers mostrando heartbeats y ACK.
3. Captura del servidor detectando `worker_01` desconectado mientras `worker_02` sigue activo.
4. Captura de la reconexion de `worker_01`.

> Las evidencias se incorporaran cuando se realicen las pruebas finales del equipo.

## Actividad 2: TCP multihilo (Isma)

El codigo de Isma esta en [Actividad2_TCP](Actividad2_TCP/README.md), con el servidor TCP, los Workers y las instrucciones para probarlos. Utiliza el puerto TCP `5002` para no interferir con el canal UDP `5001` de la Actividad 1. Los comandos de trabajo son simulados y queda pendiente integrar las actividades en los scripts finales.
