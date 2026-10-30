"""Canned outputs so the full stack can be demoed without API keys."""
from app.schemas import Grounding, Reasoning, SearchHit, StateJSON


def mock_state() -> StateJSON:
    return StateJSON(
        primary_root_cause="Redis pod OOMKilled (memory limit 512Mi) causing repeated restarts and lost connections",
        secondary_effects=[
            "redis.exceptions.ConnectionError in api-gateway",
            "Celery workers retrying and backlogging",
            "HTTP 503s on /checkout",
            "Liveness probe failures on redis-master-0",
        ],
        dependency_chain=["redis-master-0", "api-gateway", "celery-worker", "checkout-service"],
        severity="critical",
        recommended_search_query="kubernetes redis pod OOMKilled maxmemory limit 512Mi connection refused fix",
    )


def mock_grounding(query: str) -> Grounding:
    return Grounding(
        provider="tavily (mock)",
        query=query,
        answer="Set Redis maxmemory below the container memory limit and configure an eviction policy.",
        results=[
            SearchHit(title="Redis memory optimization", url="https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/",
                      snippet="Set maxmemory and a maxmemory-policy to keep Redis within its memory budget.", score=0.92),
            SearchHit(title="Kubernetes: Resource Management for Pods", url="https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
                      snippet="A container exceeding its memory limit may be OOM-killed by the kernel.", score=0.88),
        ],
    )


def mock_reasoning() -> Reasoning:
    return Reasoning(
        root_cause_analysis="redis-master-0 exceeds its 512Mi cgroup limit because Redis has no maxmemory set, so the kernel OOM-kills it. Each restart drops connections, which cascades through api-gateway and Celery into checkout 503s.",
        remediation_plan=[
            "Set Redis maxmemory to ~75% of the container limit and maxmemory-policy allkeys-lru.",
            "Raise the pod memory limit/request to match real working-set size.",
            "Add client retry with exponential backoff in api-gateway.",
            "Alert on container_memory_working_set_bytes > 85% of limit.",
        ],
        fix_recommendation="redis-server --maxmemory 384mb --maxmemory-policy allkeys-lru  # and set resources.limits.memory: 1Gi",
        confidence_score=0.86,
    )
