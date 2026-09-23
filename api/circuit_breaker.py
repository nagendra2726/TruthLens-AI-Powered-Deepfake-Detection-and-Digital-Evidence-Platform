"""
Circuit Breaker Pattern implementation for DeepSafe microservice communication.
Protects the API gateway from cascading failures and excessive latency when
individual model microservices are down or unresponsive.
"""

import time
import logging
from enum import Enum
from typing import Dict, Optional, Callable, Any

logger = logging.getLogger("deepsafe.circuit_breaker")


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Service failed: fail fast immediately
    HALF_OPEN = "HALF_OPEN"  # Probe state: test if service recovered


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        per_call_timeout: float = 8.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.per_call_timeout = per_call_timeout

        self.state = CircuitState.CLOSED
        self.consecutive_failures = 0
        self.last_state_change = time.time()
        self.last_failure_time = 0.0

    def can_execute(self) -> bool:
        """Determines if a request should be dispatched to the microservice."""
        now = time.time()
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if now - self.last_state_change >= self.recovery_timeout:
                logger.info(f"[CircuitBreaker:{self.name}] Recovery timeout expired. Transitioning OPEN -> HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def record_success(self):
        """Records a successful call, resetting failure counters."""
        if self.state != CircuitState.CLOSED:
            logger.info(f"[CircuitBreaker:{self.name}] Microservice call succeeded. Transitioning {self.state} -> CLOSED")
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
        self.consecutive_failures = 0

    def record_failure(self, error: Optional[Exception] = None):
        """Records a call failure/timeout, transitioning to OPEN if threshold exceeded."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        logger.warning(
            f"[CircuitBreaker:{self.name}] Call failure #{self.consecutive_failures} (Threshold: {self.failure_threshold}). "
            f"Error: {error}"
        )

        if self.state == CircuitState.HALF_OPEN or self.consecutive_failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(
                    f"[CircuitBreaker:{self.name}] Failure threshold reached. Transitioning {self.state} -> OPEN. "
                    f"Will fail-fast for {self.recovery_timeout}s."
                )
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()


class CircuitBreakerRegistry:
    _instances: Dict[str, CircuitBreaker] = {}

    @classmethod
    def get_breaker(
        cls,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        per_call_timeout: float = 8.0,
    ) -> CircuitBreaker:
        if name not in cls._instances:
            cls._instances[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                per_call_timeout=per_call_timeout,
            )
        return cls._instances[name]

    @classmethod
    def get_all_states(cls) -> Dict[str, Dict[str, Any]]:
        return {
            name: {
                "state": cb.state.value,
                "consecutive_failures": cb.consecutive_failures,
                "per_call_timeout_seconds": cb.per_call_timeout,
                "last_failure_time": cb.last_failure_time,
            }
            for name, cb in cls._instances.items()
        }
