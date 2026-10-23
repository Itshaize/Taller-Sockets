# Taller de Sockets: UDP y TCP

**Universidad:** Universidad Politecnica Salesiana (UPS)  
**Integrantes:** Mauricio Jacome (MAU), Isma y Dio.

Este repositorio reunira las tres actividades del taller de sockets. Por ahora se incluyen la **Actividad 1: comunicacion UDP** y la **Actividad 2: TCP multihilo**.

## Distribucion del trabajo

- **MAU - Actividad 1 (implementada):** heartbeats UDP, registro de workers, respuesta ACK y deteccion de desconexiones.
- **Isma - Actividad 2 (implementacion inicial en `Actividad2_TCP/`, pendiente de integracion):** servidor TCP multihilo y comunicacion de comandos/resultados.
- **Dio - Actividad 3 (implementacion inicial en Actividad3_Rafaga/, pendiente de integracion):** coordinacion de tareas, carga controlada y reportes.

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

## Actividad 3: Rafaga sincronizada (Dio)

Se incorpora el modulo de coordinacion, prueba de carga exclusivamente local y reportes en [Actividad3_Rafaga](Actividad3_Rafaga/README.md). Puede probarse con un Master y dos Workers de demostracion, de manera independiente. La integracion final con los modulos UDP y TCP del equipo queda pendiente. No ejecutar simultaneamente los dos Masters TCP de demostracion, pues usan el puerto 5002.

## Version integrada para el taller

Los archivos `master.py` y `worker.py` de la raiz unen las tres actividades. Los archivos de las carpetas `Actividad1_UDP`, `Actividad2_TCP` y `Actividad3_Rafaga` se conservan para documentar lo que hizo cada integrante.

**Requisitos:** Python 3.10 o superior; no se necesitan paquetes externos. Usar cuatro terminales desde la raiz del repositorio:

```bash
# Terminal 1: servidor de pruebas local de Dio
python3 Actividad3_Rafaga/objetivo_local.py

# Terminal 2: Master integrado
python3 master.py

# Terminal 3: Worker uno
python3 worker.py worker1

# Terminal 4: Worker dos
python3 worker.py worker2
```

En el menu de Master, usar **1** para comprobar registro UDP y TCP, **2** para enviar comandos (STATUS, FETCH_LOGS o EXEC_TASK) y **4** para ejecutar la prueba de carga local coordinada de 1 a 10 segundos. La prueba solo utiliza 127.0.0.1:9100 (TCP) y 127.0.0.1:9101 (UDP). Para verificar la deteccion de caidas, detener un Worker con Ctrl+C y observar el registro UDP tras unos seis segundos.

**Puertos:** UDP 5001 para heartbeats, TCP 5002 para control, 9100/9101 para el objetivo local. No ejecutar simultaneamente los servidores `Actividad2_TCP/tcp_manager.py` ni `Actividad3_Rafaga/demo_master.py` con `master.py`, porque utilizan TCP 5002.

**Integracion:** para una tarea sincronizada se seleccionan Workers registrados tanto en TCP como en UDP, se envia una orden con un instante de inicio comun y se recogen reportes de carga. El modulo de Dio mantiene sus limites de carga para evitar trafico externo. En equipos distintos, la restriccion al objetivo 127.0.0.1 significa que cada Worker prueba su propio equipo; la demostracion recomendada se hace con todos los procesos en la misma maquina. Quedan pendientes las pruebas finales de todo el grupo y sus capturas: no se afirma aqui que el sistema integrado haya sido probado en el equipo del alumno.
