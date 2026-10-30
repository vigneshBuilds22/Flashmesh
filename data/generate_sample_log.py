"""Generates data/sample_logs/k8s_redis_oom.log (~28k tokens). Run: python generate_sample_log.py"""
import random
from datetime import datetime, timedelta
random.seed(7)
t = datetime(2025, 3, 14, 9, 0, 0)
out = []
def ts():
    global t
    t += timedelta(milliseconds=random.randint(40, 900))
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"
pods = ["api-gateway-7d9f8b6c5-x2k4p", "celery-worker-5c6d7f8b9-q8w2z", "checkout-svc-6b7c8d9e4-m3n5v"]
for i in range(600):
    p = random.choice(pods)
    out.append(f"{ts()} INFO  [{p}] GET /api/v1/items/{random.randint(1,9999)} 200 {random.randint(3,90)}ms trace={random.getrandbits(64):016x}")
    if i % 7 == 0:
        out.append(f"{ts()} DEBUG [kubelet] SyncLoop (PLEG): event for pod {p} containerID={random.getrandbits(128):032x}")
    if i % 11 == 0:
        out.append(f"{ts()} INFO  [redis-master-0] DB 0: {random.randint(400000,900000)} keys, used_memory={random.randint(380,500)}MB")
    if i == 380:
        out += [
            f"{ts()} WARN  [redis-master-0] Can't save in background: fork: Cannot allocate memory",
            f"{ts()} WARN  [kubelet] Container redis in pod redis-master-0 exceeded memory limit 512Mi",
            f"{ts()} ERROR [kubelet] Container redis terminated: reason=OOMKilled exitCode=137",
            f"{ts()} WARN  [kubelet] Back-off restarting failed container redis in pod redis-master-0",
        ]
    if i > 380 and i % 5 == 0:
        p = random.choice(pods[:2])
        out += [
            f"{ts()} ERROR [{p}] redis.exceptions.ConnectionError: Error 111 connecting to redis-master:6379. Connection refused.",
            "Traceback (most recent call last):",
            '  File "/app/services/cache.py", line 88, in get_session',
            "    return self.client.get(key)",
            '  File "/usr/local/lib/python3.11/site-packages/redis/client.py", line 1329, in get',
            "    return self.execute_command('GET', name, **options)",
            "redis.exceptions.ConnectionError: Error 111 connecting to redis-master:6379. Connection refused.",
            f"{ts()} ERROR [checkout-svc-6b7c8d9e4-m3n5v] HTTP 503 POST /checkout upstream api-gateway unavailable req={random.getrandbits(64):016x}",
            f"{ts()} WARN  [celery-worker-5c6d7f8b9-q8w2z] Task orders.process[{random.getrandbits(64):016x}] retry: Retry in {random.randint(2,60)}s",
        ]
open("sample_logs/k8s_redis_oom.log", "w").write("\n".join(out) + "\n")
print(len(out), "lines")
