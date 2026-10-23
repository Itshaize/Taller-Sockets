# Actividad 3 — Ráfaga sincronizada (DIO)

**Objetivo:** el Master envía una misma tarea a varios Workers, coordina su inicio y reúne los resultados de la carga de prueba TCP/UDP.

## Archivos
- **actividad3.py**: funciones reutilizables para crear y validar órdenes, ejecutar cargas locales y resumir reportes.
- **demo_master.py**: servidor TCP de demostración; envía órdenes y recibe STRESS_READY/STRESS_RESULT.
- **demo_worker.py**: cliente persistente que recibe la orden y ejecuta la prueba en un hilo separado.
- **objetivo_local.py**: servicio local que responde PONG a mensajes PING por TCP y UDP.
- **tests/test_actividad3.py**: pruebas automáticas.

## Ejecución (cuatro terminales)
Desde la carpeta Actividad3_Rafaga y con Python 3.10 o superior:

    # Terminal 1
    python3 objetivo_local.py
    # Terminal 2
    python3 demo_master.py
    # Terminal 3
    python3 demo_worker.py worker-A
    # Terminal 4
    python3 demo_worker.py worker-B

En la terminal 2 del Master, ejecutar:

    list
    stress 5

Para una prueba automática: iniciar primero el objetivo local y ejecutar el Master con:

    python3 demo_master.py --auto 5 --workers 2

Después iniciar los dos Workers. Ejecutar las pruebas unitarias con:

    python3 -m unittest discover -s tests -v

## Comunicación y sincronización
- El Master TCP escucha en 127.0.0.1:5002 en la demostración.
- El servicio objetivo escucha en 127.0.0.1:9100 (TCP) y 127.0.0.1:9101 (UDP).
- Los mensajes TCP se codifican como una línea JSON por mensaje, terminada en salto de línea.
- El Master manda BROADCAST_STRESS con un task_id, start_at común, duración, dirección de objetivo y límites de carga.
- Cada Worker responde STRESS_READY y lanza un hilo de ejecución; al finalizar devuelve STRESS_RESULT con cantidades, latencias y hora real de inicio.
- El Master resume peticiones correctas, fallidas, latencia ponderada y diferencia entre comienzos de Workers.

Ejemplo de orden:

    {"tipo":"BROADCAST_STRESS","task_id":"abc123","start_at":1792790000.0,"duration":5,"target_ip":"127.0.0.1","rps_limit":12,"concurrency_limit":2}

## Integración pendiente con las actividades 1 y 2
Esta carpeta es un módulo comprobable de manera independiente; **no sustituye** el servidor UDP de MAU ni el TCP multihilo de Isma. La demostración usa también el puerto TCP 5002: **no ejecutar a la vez** demo_master.py y el servidor TCP de Isma en la misma máquina.

- En el Master TCP de Isma, llamar crear_orden(task_id, duracion, time.time()+3), enviar la orden JSON por el canal persistente a los Workers y recibir STRESS_READY, STRESS_RESULT y STRESS_ERROR.
- En el Worker TCP de Isma, llamar validar_orden y lanzar un hilo para ejecutar_carga_local. El hilo lector TCP no debe bloquearse esperando la prueba.
- Para coordinar con MAU, cruzar los Workers con conexión TCP activa y los que aún figuren activos en la tabla de heartbeats UDP. La detección a 6 s continúa independiente.
- En equipos separados se deben sincronizar los relojes (p. ej., NTP) para que start_at represente un instante similar.

## Alcance seguro de la simulación
El objetivo de carga se limita por código a 127.0.0.1; duración máxima 10 segundos; hasta 12 solicitudes/s por Worker y 2 tareas de red concurrentes. No se permite indicar direcciones de terceros. Se trata de una simulación acotada, no de una herramienta para saturar redes.

## Evidencias
La salida del Master muestra la lista de Workers, el identificador común de la tarea, confirmaciones STRESS_READY, reportes STRESS_RESULT y resumen final. La prueba local está documentada en EVIDENCIA_PRUEBA_LOCAL.txt. Las capturas de la integración final con las actividades de MAU e Isma deben realizarse después.
