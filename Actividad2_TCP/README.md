# Actividad 2: TCP multihilo y comandos

**Responsable:** Isma (Integrante 2)

Esta parte del taller permite que el Master reciba varias conexiones TCP al mismo tiempo y envie comandos a los Workers. Cada Worker ejecuta la tarea en un hilo y devuelve la respuesta en JSON.

## Archivos

- `tcp_manager.py`: servidor TCP, registro de Workers y menu de comandos.
- `tcp_worker.py`: cliente TCP que recibe comandos y responde.

## Como ejecutar en Ubuntu

Se necesita Python 3. No hay dependencias externas.

Desde la raiz del repositorio, abrir cuatro terminales:

**Terminal 1 (Master):**
```bash
cd Actividad2_TCP
python3 tcp_manager.py
```

**Terminales 2, 3 y 4 (Workers):**
```bash
cd Actividad2_TCP
python3 tcp_worker.py worker1
```
```bash
cd Actividad2_TCP
python3 tcp_worker.py worker2
```
```bash
cd Actividad2_TCP
python3 tcp_worker.py worker3
```

En el menu del Master, elegir `1` para listar conexiones o `2` para enviar un comando.

## Comandos de prueba

- `STATUS`: responde que el Worker esta activo.
- `FETCH_LOGS`: devuelve un registro **simulado**, no lee logs reales.
- `EXEC_TASK`: espera 5 segundos en un hilo para demostrar que la conexion no se bloquea.

Prueba recomendada: enviar `EXEC_TASK` a `worker1` y enseguida `STATUS` al mismo Worker. Se puede recibir STATUS antes de que termine la tarea anterior.

## Protocolo TCP

Los mensajes son JSON codificados en UTF-8 y terminados en un salto de linea (`\\n`). Ejemplos:

Registro: `{"tipo":"registro","nombre":"worker1"}`

Confirmacion: `{"tipo":"confirmacion","datos":"Registro correcto"}`

Comando: `{"tipo":"comando","accion":"STATUS"}`

Resultado: `{"tipo":"resultado","datos":"Worker activo y funcionando"}`

**Puerto TCP:** 5002. **IP:** 127.0.0.1 para pruebas en una sola computadora.

## Estado y limites

Esta es la implementacion inicial de la Actividad 2 y todavia esta separada del sistema UDP de la Actividad 1. Falta integrar los modulos en `master.py` y `worker.py` finales. Los comandos de trabajo son pruebas simuladas; se deben completar las pruebas de integracion y registrar evidencias. No se ha verificado el funcionamiento de este codigo en el equipo del estudiante.

## Trazabilidad

Los archivos de esta carpeta corresponden a la contribucion del Integrante 2. Los commits de GitHub permiten revisar los cambios por separado.
