"""
Generador de datos sinteticos v3.

Cada servicio tiene su propia "personalidad":
- checkout-api:     alto trafico, latencia moderada, crece con el tiempo (necesita escala)
- auth-service:     trafico estable pero con picos en login masivo, latencia critica
- search-api:       latencia alta, comportamiento bimodal (cache hit vs miss)
- billing-worker:   batch nocturno, trafico en rafagas, latencia muy alta en runs
- notifications:    trafico bajo pero sostenido, estable

Ademas incluye:
- Incidentes por horario (lunes 9-11am, viernes 17-19pm, etc)
- Outliers reales (picos de trafico = incidentes, NO errores tecnicos)
- Errores tecnicos reales (latencias negativas, NaN)
- Datos faltantes realistas (~1% NaN en categoricas, ~0.3% en numericas)
- Comportamiento semanal (finde con menos trafico)
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(seed=42)

# Configuracion realista por servicio (la "personalidad")
# Cada servicio tiene su baseline, su amplitud de ciclo diario,
# su sensibilidad a incidentes, y su patron de degradacion.
SERVICES = {
    "checkout-api": {
        "base_cpu": 38, "base_mem": 62, "base_lat": 110, "base_rps": 1200,
        "amplitude_cpu": 22, "amplitude_mem": 5, "amplitude_lat": 70, "amplitude_rps": 900,
        "incident_sensitivity": 0.18,   # probabilidad alta de tener incidentes
        "incident_magnitude": 1.6,      # picos medianos-grandes
        "weekly_drop": 0.35,            # finde baja 35%
        "drift": 0.00018,                # crece lentamente con el tiempo
        "description": "Alto trafico, crece ~2% por semana",
    },
    "auth-service": {
        "base_cpu": 28, "base_mem": 50, "base_lat": 85, "base_rps": 600,
        "amplitude_cpu": 12, "amplitude_mem": 4, "amplitude_lat": 45, "amplitude_rps": 400,
        "incident_sensitivity": 0.08,   # eventos raros pero agudos
        "incident_magnitude": 2.4,      # picos MUY fuertes (login masivo)
        "weekly_drop": 0.20,            # finde baja un poco
        "drift": 0.00005,
        "description": "Estable, picos agudos en login masivo",
    },
    "search-api": {
        "base_cpu": 48, "base_mem": 70, "base_lat": 240, "base_rps": 450,
        "amplitude_cpu": 15, "amplitude_mem": 6, "amplitude_lat": 180, "amplitude_rps": 250,
        "incident_sensitivity": 0.10,
        "incident_magnitude": 1.3,
        "weekly_drop": 0.50,            # finde baja la mitad
        "drift": 0.00008,
        "description": "Bimodal: cache hit rapido, cache miss lento",
    },
    "billing-worker": {
        "base_cpu": 18, "base_mem": 45, "base_lat": 380, "base_rps": 50,
        "amplitude_cpu": 35, "amplitude_mem": 15, "amplitude_lat": 600, "amplitude_rps": 90,
        "incident_sensitivity": 0.14,
        "incident_magnitude": 1.8,
        "weekly_drop": 0.65,            # casi no hay fin de semana
        "drift": 0.00003,
        "description": "Batch nocturno, rafagas, fin de semana casi vacio",
    },
    "notifications": {
        "base_cpu": 15, "base_mem": 40, "base_lat": 60, "base_rps": 320,
        "amplitude_cpu": 8, "amplitude_mem": 3, "amplitude_lat": 30, "amplitude_rps": 200,
        "incident_sensitivity": 0.06,
        "incident_magnitude": 1.5,
        "weekly_drop": 0.30,
        "drift": 0.00002,
        "description": "Tráfico bajo y estable, sin sorpresas",
    },
}

REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]
ENVS = ["prod", "prod", "prod", "staging"]

START = pd.Timestamp("2026-08-01")
END = pd.Timestamp("2026-09-15")
minutes = pd.date_range(START, END, freq="min")

# =============================================================================
# Generacion de ventanas de incidentes realistas (las "horas feas")
# =============================================================================
def generate_incident_windows():
    """Genera ~25 incidentes a lo largo del periodo, cada uno con duracion e intensidad."""
    windows = []
    total_minutes = len(minutes)
    n_incidents = rng.integers(20, 30)

    for _ in range(n_incidents):
        # Duracion entre 8 min y 90 min
        dur = int(rng.integers(8, 90))
        # Comienzo aleatorio
        start = int(rng.integers(0, total_minutes - dur))

        # Peso por dia de la semana (mas incidentes lunes y viernes)
        ts_start = minutes[start]
        dow = ts_start.dayofweek  # 0=lunes
        # 60% mas probable en lunes (0) o viernes (4)
        if dow in [0, 4] and rng.random() < 0.45:
            # Mantener
            pass
        elif dow in [5, 6] and rng.random() < 0.6:
            # Saltar al siguiente dia habil
            continue

        # Peso por hora del dia (mas incidentes en horas pico)
        hour = ts_start.hour
        if 9 <= hour <= 11 and rng.random() < 0.3:
            pass  # hora pico de la manana
        elif 17 <= hour <= 19 and rng.random() < 0.25:
            pass  # hora pico de la tarde
        elif rng.random() < 0.4:
            continue

        windows.append((start, start + dur))
    return windows


# =============================================================================
# 1. Metricas con personalidad por servicio
# =============================================================================
def synth_metrics() -> pd.DataFrame:
    rows = []
    incident_windows = generate_incident_windows()
    n = len(minutes)

    for svc, cfg in SERVICES.items():
        for region in REGIONS:
            # Variacion por region (no todas las regiones son iguales)
            region_factor = {"us-east-1": 1.0, "us-west-2": 0.85, "eu-west-1": 0.92}[region]

            for env in np.random.choice(ENVS, 1):
                t_cycle = (np.arange(n) % (60 * 24)) / (60 * 24)

                # Drift temporal (crecimiento/declinacion)
                drift_cpu = cfg["drift"] * np.arange(n)
                drift_rps = cfg["drift"] * 2 * np.arange(n)

                # Ciclo diario
                cpu = (cfg["base_cpu"] +
                       cfg["amplitude_cpu"] * np.sin(2 * np.pi * t_cycle) +
                       drift_cpu) * region_factor
                mem = (cfg["base_mem"] +
                       cfg["amplitude_mem"] * np.sin(2 * np.pi * t_cycle + 0.5)) * region_factor
                lat = (cfg["base_lat"] +
                       cfg["amplitude_lat"] * np.sin(2 * np.pi * t_cycle + 0.3)) * region_factor
                rps = (cfg["base_rps"] +
                       cfg["amplitude_rps"] * np.sin(2 * np.pi * t_cycle) +
                       drift_rps) * region_factor
                err = rng.uniform(0.0005, 0.004, n)

                # Ciclo semanal (finde menos trafico)
                dow = pd.Series(minutes).dt.dayofweek.values
                weekend_mask = (dow >= 5).astype(float)
                rps = rps * (1 - weekend_mask * cfg["weekly_drop"])

                # Ruido natural
                cpu = rng.normal(cpu, 3.5, n)
                mem = rng.normal(mem, 2.5, n)
                lat = np.clip(rng.normal(lat, 12, n), 5, None)
                rps = np.clip(rng.normal(rps, 40, n), 10, None)

                # Inyectar incidentes (picos de trafico/latencia/error)
                for s, e in incident_windows:
                    if rng.random() < cfg["incident_sensitivity"]:
                        peak = (s + e) // 2
                        spread = max(2, (e - s) // 4)
                        idx = np.arange(s, e)
                        if len(idx) == 0:
                            continue
                        # Forma de campana suave, no cuadrado
                        ramp = np.exp(-((idx - peak) ** 2) / (2 * spread ** 2))
                        cpu[idx] += cfg["amplitude_cpu"] * cfg["incident_magnitude"] * ramp
                        lat[idx] += cfg["amplitude_lat"] * cfg["incident_magnitude"] * ramp
                        err[idx] += rng.uniform(0.02, 0.08) * ramp

                # Errores tecnicos: latencias negativas, CPU > 100
                n_bad_lat = int(n * 0.004)
                bad_lat_idx = rng.choice(n, n_bad_lat, replace=False)
                lat[bad_lat_idx] = rng.uniform(-80, -1, n_bad_lat)

                n_bad_cpu = int(n * 0.002)
                bad_cpu_idx = rng.choice(n, n_bad_cpu, replace=False)
                cpu[bad_cpu_idx] = rng.uniform(105, 250, n_bad_cpu)

                # NaN intencionales
                nan_lat = rng.random(n) < 0.003
                lat[nan_lat] = np.nan
                nan_cpu = rng.random(n) < 0.002
                cpu[nan_cpu] = np.nan

                df = pd.DataFrame({
                    "ts": minutes,
                    "service": svc,
                    "region": region,
                    "env": env,
                    "cpu_pct": np.round(cpu, 2),
                    "mem_pct": np.round(mem, 2),
                    "latency_ms": np.round(lat, 1),
                    "rps": np.round(rps, 0),
                    "error_rate": np.round(err, 5),
                })
                rows.append(df)

    out = pd.concat(rows, ignore_index=True)
    out.to_csv(DATA / "metrics_timeseries.csv", index=False)
    return out


# =============================================================================
# 2. Incidentes (master record) con duracion y horario
# =============================================================================
def synth_incidents(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Genera incidentes a partir de las ventanas detectadas."""
    # Agrupamos las ventanas en incidentes individuales con metadata
    n_incidents = 35
    incident_data = []
    sensitivities = [s["incident_sensitivity"] for s in SERVICES.values()]
    s_sum = sum(sensitivities)
    probs = [x / s_sum for x in sensitivities]
    for i in range(n_incidents):
        # Servicio aleatorio segun sensibilidad normalizada
        svc = rng.choice(list(SERVICES.keys()), p=probs)
        cfg = SERVICES[svc]

        # Apertura: sesgada a horas de oficina
        ts_start = START + pd.Timedelta(minutes=int(rng.integers(0, len(minutes) - 200)))
        # Duracion entre 10 min y 4 horas
        duration = int(rng.integers(10, 240))
        ts_end = ts_start + pd.Timedelta(minutes=duration)

        # MTTR realista segun duracion
        mttr = int(duration * rng.uniform(0.7, 1.3))

        incident_data.append({
            "incident_id": f"INC-{i:04d}",
            "opened_at": ts_start,
            "resolved_at": ts_end,
            "service": svc,
            "severity": rng.choice(["SEV1", "SEV2", "SEV3"], p=[0.08, 0.32, 0.60]),
            "trigger": rng.choice(["slo_burn", "alert_cpu", "alert_latency", "alert_errors",
                                    "customer_report", "canary_regression"],
                                   p=[0.25, 0.25, 0.20, 0.15, 0.10, 0.05]),
            "mttr_min": mttr,
            "customers_affected": int(rng.integers(50, 80_000)),
            "region": rng.choice(REGIONS),
        })

    df = pd.DataFrame(incident_data).sort_values("opened_at").reset_index(drop=True)
    df.to_csv(DATA / "incidents.csv", index=False)
    return df


# =============================================================================
# 3. SLO burn (ya no se usa mucho pero lo dejo para compatibilidad)
# =============================================================================
def synth_slo_burn(incidents: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in incidents.iterrows():
        n_buckets = int(rng.integers(8, 30))
        ts = pd.date_range(row["opened_at"], periods=n_buckets, freq="5min")
        burn_5x = rng.exponential(0.05, n_buckets)
        burn_1x = rng.exponential(0.01, n_buckets)
        peak = n_buckets // 2
        window = slice(max(0, peak - 4), min(n_buckets, peak + 4))
        wlen = window.stop - window.start
        if wlen > 0:
            burn_5x[window] *= rng.uniform(8, 25, wlen)
            burn_1x[window] *= rng.uniform(3, 10, wlen)
        for i, t in enumerate(ts):
            rows.append({
                "ts": t,
                "service": row["service"],
                "incident_id": row["incident_id"],
                "burn_5x": round(float(burn_5x[i]), 5),
                "burn_1x": round(float(burn_1x[i]), 5),
            })
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "slo_burn.csv", index=False)
    return out


# =============================================================================
# 4. Automation runs con outliers REALES (jobs lentos en casos reales)
# =============================================================================
def synth_automation() -> pd.DataFrame:
    n = 1500
    JOBS = [
        "restart_pod", "scale_deployment", "purge_cache",
        "rotate_secrets", "db_vacuum", "snapshot_rds",
        "failover_drill", "cert_renewal",
    ]
    # Jobs con duracion esperada distinta
    job_base_duration = {
        "restart_pod": 8, "scale_deployment": 12, "purge_cache": 3,
        "rotate_secrets": 45, "db_vacuum": 120, "snapshot_rds": 90,
        "failover_drill": 180, "cert_renewal": 25,
    }
    job_failure_rate = {
        "restart_pod": 0.05, "scale_deployment": 0.06, "purge_cache": 0.02,
        "rotate_secrets": 0.04, "db_vacuum": 0.12, "snapshot_rds": 0.08,
        "failover_drill": 0.15, "cert_renewal": 0.03,
    }

    runs = []
    for _ in range(n):
        job = rng.choice(JOBS)
        # Distribucion realista: muchos runs rapidos, pocos lentos
        duration = np.random.lognormal(
            mean=np.log(job_base_duration[job]),
            sigma=0.6,
        )

        # Outliers positivos (5%): jobs lentos reales
        if rng.random() < 0.05:
            duration *= rng.uniform(5, 20)

        # Status con probabilidad de fallo segun el job
        p_fail = job_failure_rate[job]
        if rng.random() < 0.04:
            # timeout: duration mayor al SLA del job
            duration *= 1.5
            status = "timeout"
        elif rng.random() < p_fail:
            status = "failed"
        else:
            status = "success"

        # Errores tecnicos: duraciones negativas o > 24h
        if rng.random() < 0.01:
            duration = rng.choice([-1, -10, 86401, 100000])
        # NaN
        if rng.random() < 0.005:
            duration = np.nan

        # Retries: mas retries para fallos
        retries = 0
        if status in ("failed", "timeout"):
            retries = int(rng.integers(1, 4))

        runs.append({
            "run_id": f"R-{len(runs)+1:05d}",
            "job_name": job,
            "started_at": pd.Timestamp(START) + pd.Timedelta(minutes=int(rng.integers(0, len(minutes)))),
            "duration_sec": None if np.isnan(duration) else int(duration),
            "status": status,
            "retries": retries,
            "triggered_by": rng.choice(["alert", "schedule", "manual", "pipeline"],
                                       p=[0.40, 0.40, 0.10, 0.10]),
            "service": rng.choice(list(SERVICES.keys())),
        })

    df = pd.DataFrame(runs)
    # NaN en job_name (~0.3%)
    df.loc[rng.random(len(df)) < 0.003, "job_name"] = np.nan
    df.to_csv(DATA / "automation_runs.csv", index=False)
    return df


# =============================================================================
# 5. Tickets con distribucion realista y outliers reales
# =============================================================================
def synth_tickets() -> pd.DataFrame:
    n = 900
    CATEGORIES = ["incident", "service_request", "change", "problem"]
    PRIORITIES = ["P1", "P2", "P3", "P4"]
    TEAMS = ["payments", "identity", "platform", "data", "frontend"]

    base_resolution = {"P1": 25, "P2": 110, "P3": 360, "P4": 1200}

    rows = []
    for _ in range(n):
        priority = rng.choice(PRIORITIES, p=[0.10, 0.25, 0.40, 0.25])
        team = rng.choice(TEAMS)
        # Distribucion normal alrededor del base
        resolution = base_resolution[priority] + rng.normal(0, 50)

        # 3% tickets problematicos (incidentes graves)
        if rng.random() < 0.03:
            resolution *= rng.uniform(5, 20)

        # Errores tecnicos (1%)
        if rng.random() < 0.01:
            resolution = rng.choice([-10, -1, 0])

        # NaN
        if rng.random() < 0.02:
            priority = np.nan
        if rng.random() < 0.015:
            team = np.nan

        # Timestamps con distribucion realista (mas tickets durante horas de oficina)
        # Crear timestamp con probabilidad ponderada por hora
        n_minutes = len(minutes)
        # Peso: 0 a 6am muy bajo, 9-12am y 14-17pm alto
        weights = np.ones(n_minutes)
        for i, ts in enumerate(minutes):
            hour = ts.hour
            if 9 <= hour <= 12 or 14 <= hour <= 17:
                weights[i] = 4.0
            elif 19 <= hour <= 23:
                weights[i] = 0.5
            elif hour < 7:
                weights[i] = 0.2
            weights[i] *= 0.6 if ts.dayofweek >= 5 else 1.0
        weights /= weights.sum()
        start_idx = rng.choice(n_minutes, p=weights)

        rows.append({
            "ticket_id": f"T-{len(rows)+1:05d}",
            "created_at": minutes[start_idx],
            "category": rng.choice(CATEGORIES, p=[0.45, 0.30, 0.15, 0.10]),
            "priority": priority,
            "team": team if rng.random() >= 0.015 else np.nan,
            "sla_min": rng.choice([30, 120, 480, 1440], p=[0.10, 0.25, 0.40, 0.25]),
            "resolution_min": max(0, int(resolution)) if resolution >= 0 else int(resolution),
            "rollback": 0,
        })

    df = pd.DataFrame(rows)
    # Rollback solo en cambios (~10% de los cambios)
    change_mask = df["category"] == "change"
    df.loc[change_mask, "rollback"] = (rng.random(change_mask.sum()) < 0.10).astype(int)
    # Calcular breach de SLA
    df["sla_breached"] = (df["resolution_min"] > df["sla_min"]).astype(int)
    df.to_csv(DATA / "tickets.csv", index=False)
    return df


def main() -> None:
    print("[1/5] metrics_timeseries.csv ...", end=" ")
    m = synth_metrics()
    print(f"ok ({len(m):,} filas)")

    print("[2/5] incidents.csv ...", end=" ")
    inc = synth_incidents(m)
    print(f"ok ({len(inc)} incidentes)")

    print("[3/5] slo_burn.csv ...", end=" ")
    synth_slo_burn(inc)
    print("ok")

    print("[4/5] automation_runs.csv ...", end=" ")
    synth_automation()
    print("ok")

    print("[5/5] tickets.csv ...", end=" ")
    synth_tickets()
    print("ok")

    print(f"\nDatasets en {DATA}")
    print(f"Periodo: {START.date()} a {END.date()} ({len(minutes):,} minutos)")
    print(f"Servicios con personalidades distintas: {list(SERVICES.keys())}")


if __name__ == "__main__":
    main()