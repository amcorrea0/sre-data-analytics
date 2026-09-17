# Story — SRE Data Analytics (60 min)

## Narrativa
> Somos SREs junior. Nos llegan dashboards bonitos todos los días, pero **cuando algo
> se rompe nadie tiene el dato a mano**: ¿cuál fue el p95 real de checkout-api
> ayer? ¿Cuántos tickets del equipo payments breacharon SLA? ¿El job `db_vacuum`
> falló por bug o porque se está demorando más de lo normal?
>
> Hoy aprendemos a sacar esas respuestas nosotros mismos, **sin esperar a un
> data engineer**, y a contarlas en una sola línea que entienda un director.

## Arco narrativo (3 actos)

### Acto 1 — El “dashboard miente”
- **Tesis:** los números en PDF mienten si no miramos outliers y NaN.
- **Demostración:** histograma crudo vs limpio de `latency_ms`.
- **Pregunta detonante:** “Si el reporte dice disponibilidad 99.9%, ¿qué está ocultando?”

### Acto 2 — El toolkit del SRE
- ETL con pandas (load → clean → aggregate).
- Regla de Tukey (IQR × 1.5) por grupo.
- Boxplots en escala log.
- Heatmaps pivote.
- **Cada lab = 1 herramienta aplicada a 1 dataset real de SRE.**

### Acto 3 — La historia ejecutiva
- 1 cifra por sección.
- 1 responsable claro.
- 1 acción priorizada con RICE.
- **Voto final:** la mejor headline de la sesión.

## Ritmo emocional
- 0–5 min: expectativa (qué vamos a lograr).
- 5–17 min: confianza (sigue los pasos del facilitador).
- 17–29 min: confianza (repite con variación).
- 29–41 min: descubrimiento (manos a la obra).
- 41–53 min: ownership (presentan su número).
- 53–60 min: orgullo (mural + voto).

## Promesa de aprendizaje
Al terminar, cada SRE puede:
- Diagnosticar NaN y errores técnicos en un CSV en menos de 5 minutos.
- Aplicar Tukey por grupo y explicar por qué mediana > media para imputar.
- Construir 4 figuras listas para presentar.
- Redactar una headline ejecutiva verificable.