"""Generates two SYNTHETIC incident logs for the validation harness (deployment + traffic).
Replace them with real incident logs of the same names for a stronger demo.
Run from data/:  python generate_validation_logs.py"""
import random
from datetime import datetime, timedelta

random.seed(11)


def make(path, start, normal_line, incident_at, incident_lines, burst, n=700):
    t = start
    out = []

    def ts():
        nonlocal t
        t += timedelta(milliseconds=random.randint(40, 700))
        return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"

    for i in range(n):
        out.append(normal_line(ts))
        if i == incident_at:
            out += [l(ts) for l in incident_lines]
        if i > incident_at and i % 4 == 0:
            out += [l(ts) for l in burst]
    open(path, "w").write("\n".join(out) + "\n")
    print(path, len(out), "lines")


rid = lambda: f"{random.getrandbits(64):016x}"

# --- Deployment failure: checkout-svc v2.4.0 crashes on a missing config key -------------
make(
    "sample_logs/bad_release_checkout.log", datetime(2025, 4, 2, 14, 0, 0),
    lambda ts: f"{ts()} INFO  [checkout-svc-v2-3-9] POST /checkout 200 {random.randint(20,90)}ms trace={rid()}",
    350,
    [
        lambda ts: f"{ts()} INFO  [deploy] Rolling out checkout-svc release v2.4.0 (previous: v2.3.9)",
        lambda ts: f"{ts()} ERROR [checkout-svc-v2-4-0] KeyError: 'PAYMENT_GATEWAY_URL' (config.py line 41, load_settings)",
        lambda ts: f"{ts()} ERROR [kubelet] Container checkout-svc in pod checkout-svc-v2-4-0-abc12 CrashLoopBackOff exitCode=1",
    ],
    [
        lambda ts: f"{ts()} ERROR [ingress] HTTP 502 POST /checkout upstream checkout-svc has no healthy endpoints req={rid()}",
        lambda ts: f"{ts()} WARN  [kubelet] Back-off restarting failed container checkout-svc (release v2.4.0)",
        lambda ts: f"{ts()} ERROR [checkout-svc-v2-4-0] KeyError: 'PAYMENT_GATEWAY_URL' (config.py line 41, load_settings)",
    ],
)

# --- Traffic failure: api-gateway saturated at HPA max (3 replicas) ----------------------
make(
    "sample_logs/traffic_spike_gateway.log", datetime(2025, 5, 9, 18, 0, 0),
    lambda ts: f"{ts()} INFO  [api-gateway-{random.randint(0,2)}] GET /api/v1/items 200 {random.randint(5,40)}ms rps={random.randint(180,260)} trace={rid()}",
    350,
    [
        lambda ts: f"{ts()} WARN  [ingress] Request rate jumped to 2400 rps (baseline 220 rps) after marketing campaign launch",
        lambda ts: f"{ts()} WARN  [hpa] api-gateway at maxReplicas=3, desired=14, cannot scale further",
    ],
    [
        lambda ts: f"{ts()} WARN  [api-gateway-{random.randint(0,2)}] CPU throttled 97% (limit 500m) queue_depth={random.randint(800,3000)}",
        lambda ts: f"{ts()} ERROR [ingress] HTTP 504 GET /api/v1/items upstream api-gateway timed out after 30s req={rid()}",
        lambda ts: f"{ts()} ERROR [api-gateway-{random.randint(0,2)}] worker pool exhausted: 64/64 busy, rejecting request",
    ],
)
