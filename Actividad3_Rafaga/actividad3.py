"""Actividad 3: coordinación y carga de red exclusivamente local."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ipaddress
import math
import socket
import statistics
import time
from typing import Any

TCP_PORT = 9100
UDP_PORT = 9101
MAX_DURATION = 10
MAX_RPS = 12
MAX_CONCURRENCY = 2


def verificar_objetivo(host: str) -> str:
    """Las pruebas solo pueden dirigirse al objetivo local del laboratorio."""
    if not isinstance(host, str):
        raise ValueError("Objetivo inválido")
    if host.lower() == "localhost":
        return "127.0.0.1"
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("Solo se permite 127.0.0.1.") from exc
    if str(address) != "127.0.0.1":
        raise ValueError("Esta práctica solo admite 127.0.0.1.")
    return str(address)


def crear_orden(task_id: str, duracion: int, inicio: float, host: str = "127.0.0.1") -> dict[str, Any]:
    if isinstance(duracion, bool) or not isinstance(duracion, int) or not 1 <= duracion <= MAX_DURATION:
        raise ValueError(f"La duración debe estar entre 1 y {MAX_DURATION} segundos.")
    if not isinstance(inicio, (float, int)) or not math.isfinite(inicio):
        raise ValueError("Instante de inicio no válido.")
    return {
        "tipo": "BROADCAST_STRESS",
        "task_id": str(task_id),
        "start_at": float(inicio),
        "duration": duracion,
        "target_ip": verificar_objetivo(host),
        "rps_limit": MAX_RPS,
        "concurrency_limit": MAX_CONCURRENCY,
    }


def validar_orden(orden: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(orden, dict) or orden.get("tipo") != "BROADCAST_STRESS":
        raise ValueError("Tipo de orden inválido.")
    inicio = orden.get("start_at")
    duracion = orden.get("duration")
    rps = orden.get("rps_limit")
    concurrencia = orden.get("concurrency_limit")
    if isinstance(duracion, bool) or not isinstance(duracion, int) or not 1 <= duracion <= MAX_DURATION:
        raise ValueError("Duración no permitida.")
    if isinstance(rps, bool) or not isinstance(rps, int) or not 1 <= rps <= MAX_RPS:
        raise ValueError("Tasa de solicitudes no permitida.")
    if isinstance(concurrencia, bool) or not isinstance(concurrencia, int) or not 1 <= concurrencia <= MAX_CONCURRENCY:
        raise ValueError("Concurrencia no permitida.")
    if not isinstance(inicio, (int, float)) or not math.isfinite(inicio):
        raise ValueError("Inicio no válido.")
    if not isinstance(orden.get("task_id"), str) or not orden["task_id"]:
        raise ValueError("Falta el identificador de tarea.")
    verificar_objetivo(orden.get("target_ip", ""))
    return orden


def _enviar_peticion(host: str, protocolo: str) -> tuple[bool, float, str]:
    inicio = time.perf_counter()
    try:
        if protocolo == "TCP":
            with socket.create_connection((host, TCP_PORT), timeout=0.6) as conexion:
                conexion.settimeout(0.6)
                conexion.sendall(b"PING")
                if conexion.recv(4) != b"PONG":
                    raise OSError("Respuesta TCP incorrecta")
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
                conexion.settimeout(0.6)
                conexion.sendto(b"PING", (host, UDP_PORT))
                if conexion.recvfrom(4)[0] != b"PONG":
                    raise OSError("Respuesta UDP incorrecta")
        return True, (time.perf_counter() - inicio) * 1000, ""
    except OSError as exc:
        return False, (time.perf_counter() - inicio) * 1000, type(exc).__name__


def ejecutar_carga_local(orden: dict[str, Any], node_id: str) -> dict[str, Any]:
    """Enviar PING TCP/UDP al objetivo local usando un inicio común."""
    validar_orden(orden)
    host = verificar_objetivo(orden["target_ip"])
    retraso = orden["start_at"] - time.time()
    if retraso > 0:
        time.sleep(retraso)
    inicio_real = time.time()
    inicio_mono = time.monotonic()
    fin_mono = inicio_mono + orden["duration"]
    tasa = orden["rps_limit"]
    presupuesto = orden["duration"] * tasa

    def enviar(i: int) -> dict[str, Any] | None:
        programado = inicio_mono + i / tasa
        tiempo_espera = programado - time.monotonic()
        if tiempo_espera > 0:
            time.sleep(tiempo_espera)
        if time.monotonic() >= fin_mono:
            return None
        protocolo = "TCP" if i % 2 == 0 else "UDP"
        ok, latencia, error = _enviar_peticion(host, protocolo)
        return {"protocolo": protocolo, "ok": ok, "lat_ms": latencia, "error": error}

    with ThreadPoolExecutor(max_workers=orden["concurrency_limit"]) as pool:
        muestras = [dato for dato in pool.map(enviar, range(presupuesto)) if dato is not None]
    fin_real = time.time()
    enviados = len(muestras)
    correctos = sum(item["ok"] for item in muestras)
    latencias = sorted(item["lat_ms"] for item in muestras if item["ok"])
    duracion_real = max(0.001, fin_real - inicio_real)
    errores = sorted(set(item["error"] for item in muestras if item["error"]))
    return {
        "tipo": "STRESS_RESULT",
        "task_id": orden["task_id"],
        "node_id": node_id,
        "scheduled_at": orden["start_at"],
        "started_at": round(inicio_real, 4),
        "finished_at": round(fin_real, 4),
        "duration_real_s": round(duracion_real, 3),
        "sent": enviados,
        "ok": correctos,
        "failed": enviados - correctos,
        "tcp_ok": sum(item["ok"] and item["protocolo"] == "TCP" for item in muestras),
        "udp_ok": sum(item["ok"] and item["protocolo"] == "UDP" for item in muestras),
        "avg_latency_ms": round(statistics.mean(latencias), 3) if latencias else None,
        "p95_latency_ms": round(latencias[math.ceil(0.95 * len(latencias)) - 1], 3) if latencias else None,
        "throughput_ok_s": round(correctos / duracion_real, 2),
        "errors": errores[:3],
    }


def resumir_reportes(reportes: list[dict[str, Any]]) -> dict[str, Any]:
    enviados = sum(x["sent"] for x in reportes)
    ok = sum(x["ok"] for x in reportes)
    medias = [(x["avg_latency_ms"], x["ok"]) for x in reportes if x["avg_latency_ms"] is not None and x["ok"]]
    lat_media = sum(media * n for media, n in medias) / sum(n for _, n in medias) if medias else None
    inicios = [x["started_at"] for x in reportes]
    return {
        "workers_con_resultado": len(reportes),
        "peticiones_enviadas": enviados,
        "peticiones_correctas": ok,
        "peticiones_fallidas": enviados - ok,
        "tasa_exito_pct": round((ok / enviados) * 100, 2) if enviados else 0,
        "latencia_media_ponderada_ms": round(lat_media, 3) if lat_media is not None else None,
        "diferencia_inicio_ms": round((max(inicios) - min(inicios)) * 1000, 1) if len(inicios) > 1 else 0,
    }
