from mitmproxy import http
from pathlib import Path
from datetime import datetime, timezone
import json

LOG_PATH = Path(r'D:\OneDrive - Hogeschool Rotterdam\SURF_PILOT\AI_HUB_PILOT\WILLMA_STRESS_TESTS\assets\proxy\mitmproxy.log')
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _write_event(stage: str, flow: http.HTTPFlow):
	event = {
		"timestamp_utc": datetime.now(timezone.utc).isoformat(),
		"stage": stage,
		"method": flow.request.method,
		"url": flow.request.pretty_url,
		"path": flow.request.path,
		"status_code": None if flow.response is None else flow.response.status_code,
		"has_api_key": "X-API-KEY" in flow.request.headers,
		"user_agent": flow.request.headers.get("User-Agent", ""),
	}
	with LOG_PATH.open("a", encoding="utf-8") as handle:
		handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def request(flow: http.HTTPFlow):
	_write_event("request", flow)


def response(flow: http.HTTPFlow):
	_write_event("response", flow)
