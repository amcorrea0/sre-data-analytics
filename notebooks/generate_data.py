"""
Generador de datasets sinteticos para los labs de SRE Data Analytics v2.

Cambios vs. v1:
- Outliers reales (incidentes / jobs lentos) con magnitudes grandes.
- Datos faltantes intencionales (NaN) para practicar limpieza.
- "Errores tecnicos" (valores imposibles: negativos, fuera de rango) para
  distinguir de outliers de negocio.
- Campos extra para graficar: ts escalado, region, env.

Uso:
    python notebooks/generate_data.py

Salida en data/: 5 CSV (~22-25 MB en total).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(seed=42)

SERVICES = ["checkout-api", "auth-service", "search-api", "billing-worker", "notifications"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1"]
ENVS = ["prod", "prod", "prod", "staging"]
START = pd.Timestamp("2026-08-01")
END = pd.Timestamp("2026-09-15")
minutes = pd.date_range(START, END, freq="min")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _inject_missingness(df: pd.DataFrame, cols: list[str], p: float) -> pd.DataFrame:
    """Inserta NaN aleatorios en cols para practicar limpieza."""
    mask = rng.random(df.shape[0]) < p
    for c in cols:
        df.loc[mask, c] = np.nan
    return df


# ---------------------------------------------------------------------------
# 1. Observabilidad: métricas + NaN + outliers + SLO
# ---------------------------------------------------------------------------
def synth_metrics() -> pd.DataFrame:
    """Series por (servicio, region, env) con baseline + ciclo diario + picos.

    Outliers de dos tipos:
    - Tecnicos (imposibles): latencia < 0, cpu > 100. Borrar.
    - De negocio (incidentes): p95 elevado y error_rate alto. Mantener y analizar.
    """
    rows = []
    for svc in SERVICES:
        for region in REGIONS:
            for env in np.random.choice(ENVS, 1):
                n = len(minutes)
                t = (np.arange(n) % (60 * 24)) / (60 * 24)
                # baseline con ciclo diario
                base_cpu = 35 + 15 * np.sin(2 * np.pi * t) + rng.normal(0, 2)
                base_mem = 55 + 8 * np.sin(2 * np.pi * t + 1)
                base_lat = 120 + 40 * np.sin(2 * np.pi * t + 0.5)
                base_rps = 800 + 600 * np.sin(2 * np.pi * t)

                cpu = rng.normal(base_cpu, 4, n)
                mem = rng.normal(base_mem, 3, n)
                lat = np.clip(rng.normal(base_lat, 20, n), 10, None)
                rps = np.clip(rng.normal(base_rps, 80, n), 50, None)
                err = rng.uniform(0.0005, 0.004, n)

                # 4 eventos de incidente (outliers de negocio)
                for _ in range(4):
                    s = int(rng.integers(0, n - 60))
                    cpu[s:s + 30] += rng.normal(35, 5)
                    lat[s:s + 30] += rng.normal(180, 30)
                    err[s:s + 30] += rng.uniform(0.02, 0.06)

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

                # 0.5% "errores tecnicos": negativos o > 100
                bad = rng.random(n) < 0.005
                df.loc[bad, "latency_ms"] = rng.uniform(-50, -1, bad.sum()).round(1)
                bad_cpu = rng.random(n) < 0.002
                df.loc[bad_cpu, "cpu_pct"] = rng.uniform(110, 250, bad_cpu.sum()).round(2)

                # 0.3% NaN en latencia y cpu para practicar limpieza
                df = _inject_missingness(df, ["latency_ms"], p=0.003)
                df = _inject_missingness(df, ["cpu_pct"], p=0.002)

                rows.append(df)
    out = pd.concat(rows, ignore_index=True)
    out.to_csv(DATA / "metrics_timeseries.csv", index=False)
    return out


def synth_incidents() -> pd.DataFrame:
    n = 60
    df = pd.DataFrame({
        "incident_id": [f"INC-{i:04d}" for i in range(1, n + 1)],
        "opened_at": pd.to_datetime(rng.uniform(START.value, END.value, n), unit="ns"),
        "service": rng.choice(SERVICES, n),
        "region": rng.choice(REGIONS, n),
        "severity": rng.choice(["SEV1", "SEV2", "SEV3"], n, p=[0.1, 0.3, 0.6]),
        "trigger": rng.choice(["slo_burn", "alert_cpu", "alert_latency", "customer_report"],
                               n, p=[0.4, 0.25, 0.2, 0.15]),
        "mttr_min": rng.lognormal(mean=3.4, sigma=0.7, size=n).round(0),
        "customers_affected": rng.integers(0, 50_000, n),
    })
    df["resolved_at"] = df["opened_at"] + pd.to_timedelta(df["mttr_min"], unit="m")
    df = df.sort_values("opened_at").reset_index(drop=True)
    df.to_csv(DATA / "incidents.csv", index=False)
    return df


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


# ---------------------------------------------------------------------------
# 2. Automatización: jobs / runbooks — con outliers de duración
# ---------------------------------------------------------------------------
JOBS = [
    "restart_pod", "scale_deployment", "purge_cache",
    "rotate_secrets", "db_vacuum", "snapshot_rds",
    "failover_drill", "cert_renewal",
]


def synth_automation() -> pd.DataFrame:
    n = 1500
    duration = rng.lognormal(mean=4.0, sigma=0.9, size=n)
    # outliers positivos (jobs lentos reales, no errores tecnicos)
    heavy = rng.random(n) < 0.05
    duration[heavy] *= rng.uniform(8, 30, heavy.sum())
    # outliers imposibles (jobs negativos / > 24h) -> error tecnico
    bad = rng.random(n) < 0.01
    duration[bad] = rng.choice([-1, -10, 86401, 100000], bad.sum())

    df = pd.DataFrame({
        "run_id": [f"R-{i:05d}" for i in range(1, n + 1)],
        "job_name": rng.choice(JOBS, n),
        "started_at": pd.to_datetime(rng.uniform(START.value, END.value, n), unit="ns"),
        "duration_sec": np.round(duration, 0),
        "status": rng.choice(["success", "success", "success", "failed", "timeout"],
                             n, p=[0.78, 0.05, 0.05, 0.07, 0.05]),
        "retries": rng.choice([0, 0, 0, 0, 1, 2, 3], n),
        "triggered_by": rng.choice(["alert", "schedule", "manual", "pipeline"],
                                   n, p=[0.45, 0.35, 0.1, 0.1]),
        "service": rng.choice(SERVICES, n),
    })
    df.loc[df["status"] == "failed", "retries"] = rng.integers(1, 4, (df["status"] == "failed").sum())

    # 0.5% NaN en duration para practicar
    df = _inject_missingness(df, ["duration_sec"], p=0.005)
    # 0.3% NaN en job_name
    df = _inject_missingness(df, ["job_name"], p=0.003)

    df.to_csv(DATA / "automation_runs.csv", index=False)
    return df


# ---------------------------------------------------------------------------
# 3. Requerimientos operación: tickets + outliers + NaN
# ---------------------------------------------------------------------------
CATEGORIES = ["incident", "service_request", "change", "problem"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
TEAMS = ["payments", "identity", "platform", "data", "frontend"]


def synth_tickets() -> pd.DataFrame:
    n = 900
    base = {"P1": 25, "P2": 110, "P3": 360, "P4": 1200}
    resolution = np.array([base[p] for p in rng.choice(PRIORITIES, n)]) + rng.normal(0, 60, n)
    resolution = np.clip(resolution, 5, None)
    # outliers: tickets que tardan 5x-20x (incidentes de los lunes)
    heavy = rng.random(n) < 0.04
    resolution[heavy] *= rng.uniform(5, 20, heavy.sum())
    # errores tecnicos (negativos o 0)
    bad = rng.random(n) < 0.01
    resolution[bad] = rng.choice([-10, -1, 0], bad.sum())

    df = pd.DataFrame({
        "ticket_id": [f"T-{i:05d}" for i in range(1, n + 1)],
        "created_at": pd.to_datetime(rng.uniform(START.value, END.value, n), unit="ns"),
        "category": rng.choice(CATEGORIES, n, p=[0.45, 0.30, 0.15, 0.10]),
        "priority": rng.choice(PRIORITIES, n, p=[0.10, 0.25, 0.40, 0.25]),
        "team": rng.choice(TEAMS, n),
        "sla_min": rng.choice([30, 120, 480, 1440], n, p=[0.10, 0.25, 0.40, 0.25]),
        "resolution_min": np.round(resolution, 0),
    })
    df["sla_breached"] = (df["resolution_min"] > df["sla_min"]).astype(int)
    df["rollback"] = ((df["category"] == "change") &
                      (rng.random(n) < 0.08)).astype(int)

    # NaN en priority/team (~2%) para practicar limpieza
    df = _inject_missingness(df, ["priority"], p=0.02)
    df = _inject_missingness(df, ["team"], p=0.015)

    df.to_csv(DATA / "tickets.csv", index=False)
    return df


def main() -> None:
    print("[1/5] metrics_timeseries.csv ...", end=" ")
    synth_metrics(); print("ok")
    print("[2/5] incidents.csv ...", end=" ")
    inc = synth_incidents(); print("ok")
    print("[3/5] slo_burn.csv ...", end=" ")
    synth_slo_burn(inc); print("ok")
    print("[4/5] automation_runs.csv ...", end=" ")
    synth_automation(); print("ok")
    print("[5/5] tickets.csv ...", end=" ")
    synth_tickets(); print("ok")
    print(f"\nDatasets en {DATA}")


if __name__ == "__main__":
    main()