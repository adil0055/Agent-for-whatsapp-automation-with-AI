"""
Prometheus metrics instrumentation for TradesBot.
Exposes /metrics endpoint for Prometheus scraping.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger

log = get_logger("metrics")

# In-memory metrics counters (lightweight, no dependency)
_metrics = {
    "http_requests_total": {},       # {method_path: count}
    "http_request_duration_seconds": {},  # {method_path: [sum, count]}
    "http_errors_total": {},         # {status_code: count}
    "messages_processed_total": 0,
    "messages_failed_total": 0,
    "quotes_generated_total": 0,
    "invoices_generated_total": 0,
    "jobs_scheduled_total": 0,
    "followups_sent_total": 0,
    "voice_calls_made_total": 0,
    "ocr_processed_total": 0,
    "language_detections_total": {},  # {lang: count}
    "active_workers": 1,
}


def inc(metric: str, label: str = None, value: int = 1):
    """Increment a counter metric."""
    if label:
        if metric not in _metrics:
            _metrics[metric] = {}
        _metrics[metric][label] = _metrics[metric].get(label, 0) + value
    else:
        _metrics[metric] = _metrics.get(metric, 0) + value


def observe_duration(metric: str, label: str, duration: float):
    """Record a duration observation."""
    if label not in _metrics.get(metric, {}):
        _metrics.setdefault(metric, {})[label] = [0.0, 0]
    _metrics[metric][label][0] += duration
    _metrics[metric][label][1] += 1


def format_prometheus() -> str:
    """Format all metrics in Prometheus text exposition format."""
    lines = []

    # HTTP request counts
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    for path, count in _metrics.get("http_requests_total", {}).items():
        lines.append(f'http_requests_total{{path="{path}"}} {count}')

    # HTTP duration
    lines.append("# HELP http_request_duration_seconds HTTP request duration")
    lines.append("# TYPE http_request_duration_seconds summary")
    for path, (total, count) in _metrics.get("http_request_duration_seconds", {}).items():
        avg = total / count if count > 0 else 0
        lines.append(f'http_request_duration_seconds_sum{{path="{path}"}} {total:.4f}')
        lines.append(f'http_request_duration_seconds_count{{path="{path}"}} {count}')

    # HTTP errors
    lines.append("# HELP http_errors_total Total HTTP errors by status code")
    lines.append("# TYPE http_errors_total counter")
    for code, count in _metrics.get("http_errors_total", {}).items():
        lines.append(f'http_errors_total{{status="{code}"}} {count}')

    # Business metrics
    for metric in [
        "messages_processed_total", "messages_failed_total",
        "quotes_generated_total", "invoices_generated_total",
        "jobs_scheduled_total", "followups_sent_total",
        "voice_calls_made_total", "ocr_processed_total",
    ]:
        val = _metrics.get(metric, 0)
        lines.append(f"# HELP {metric} Total count of {metric.replace('_total', '')}")
        lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {val}")

    # Language detections
    lines.append("# HELP language_detections_total Language detections by language")
    lines.append("# TYPE language_detections_total counter")
    for lang, count in _metrics.get("language_detections_total", {}).items():
        lines.append(f'language_detections_total{{language="{lang}"}} {count}')

    # Active workers gauge
    lines.append("# HELP active_workers Number of active worker processes")
    lines.append("# TYPE active_workers gauge")
    lines.append(f"active_workers {_metrics.get('active_workers', 0)}")

    return "\n".join(lines) + "\n"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        path = request.url.path
        method = request.method
        label = f"{method} {path}"

        response = await call_next(request)

        duration = time.time() - start
        inc("http_requests_total", label)
        observe_duration("http_request_duration_seconds", label, duration)

        if response.status_code >= 400:
            inc("http_errors_total", str(response.status_code))

        return response
