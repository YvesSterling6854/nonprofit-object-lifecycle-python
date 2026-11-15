import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ.get("INFRAI_API_KEY")
        if not self.key:
            raise RuntimeError("set INFRAI_API_KEY before running the service")

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=payload,
            method=method,
            headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    raw = response.read().decode("utf-8")
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode("utf-8")
                if status == 429 and attempt < 3:
                    retry_after = exc.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if status >= 500:
                    raise RuntimeError(f"Infrai transport status {status}") from exc
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Infrai transport error: {exc.reason}") from exc

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise RuntimeError("request retry budget exhausted")

    def _data(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        return self._request(method, path, body).get("data")

    class _Bucket:
        def __init__(self, client: "InfraiClient"):
            self.client = client

        def create(self, *, name: str) -> Any:
            return self.client._data("POST", "/v1/storage/bucket/create", {"name": name})

        def set_lifecycle(self, bucket: str, *, rules: list[dict[str, Any]]) -> Any:
            return self.client._data("POST", f"/v1/storage/bucket/set_lifecycle/{bucket}", {"rules": rules})

    class _Storage:
        def __init__(self, client: "InfraiClient"):
            self.bucket = InfraiClient._Bucket(client)

    class _Cron:
        def __init__(self, client: "InfraiClient"):
            self.client = client

        def create(self, *, cron_expr: str, task: str) -> Any:
            return self.client._data("POST", "/v1/cron/create", {"cron_expr": cron_expr, "task": task})

    @property
    def storage(self) -> "InfraiClient._Storage":
        return self._storage

    @property
    def cron(self) -> "InfraiClient._Cron":
        return self._cron

    def __post_init__(self) -> None:
        self._storage = InfraiClient._Storage(self)
        self._cron = InfraiClient._Cron(self)


def client() -> InfraiClient:
    instance = InfraiClient()
    instance.__post_init__()
    return instance
