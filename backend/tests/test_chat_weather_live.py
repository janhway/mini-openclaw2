from __future__ import annotations

import json
import importlib
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pytest
from fastapi.testclient import TestClient


def _parse_provider_from_key_md(provider_name: str) -> dict[str, str]:
    key_md = Path("KEY.md").read_text(encoding="utf-8")
    lines = key_md.splitlines()
    capture = False
    result: dict[str, str] = {}

    for raw in lines:
        line = raw.strip()
        if line.startswith("## "):
            capture = provider_name.lower() in line.lower()
            continue
        if not capture:
            continue
        if line.startswith("## "):
            break
        if line.startswith("base_url="):
            result["base_url"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("api_key="):
            result["api_key"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("model="):
            result["model"] = line.split("=", 1)[1].strip().strip('"')

    return result


@dataclass
class LiveWeather:
    city_name: str
    temperature_c: float
    weather_code: int


def _fetch_live_putian_weather() -> LiveWeather:
    geo_query = urlencode({"name": "Putian", "count": 1, "language": "en", "format": "json"})
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?{geo_query}"
    with urlopen(geo_url, timeout=25) as response:
        geo_payload = json.loads(response.read().decode("utf-8"))

    results = geo_payload.get("results") or []
    if not results:
        raise AssertionError("Open-Meteo geocoding returned no Putian result")

    first = results[0]
    lat = first["latitude"]
    lon = first["longitude"]
    city_name = first.get("name", "Putian")

    forecast_query = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,weather_code",
            "timezone": "Asia/Shanghai",
        }
    )
    forecast_url = f"https://api.open-meteo.com/v1/forecast?{forecast_query}"
    with urlopen(forecast_url, timeout=25) as response:
        weather_payload = json.loads(response.read().decode("utf-8"))

    current = weather_payload.get("current") or {}
    return LiveWeather(
        city_name=city_name,
        temperature_c=float(current["temperature_2m"]),
        weather_code=int(current["weather_code"]),
    )


def _extract_temperature_c(text: str) -> float | None:
    patterns = [
        r"(-?\d+(?:\.\d+)?)\s*℃",
        r"(-?\d+(?:\.\d+)?)\s*°\s*C",
        r"气温[^0-9-]{0,8}(-?\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _weather_keywords_from_code(code: int) -> list[str]:
    if code == 0:
        return ["晴"]
    if code in {1, 2, 3}:
        return ["多云", "阴"]
    if code in {45, 48}:
        return ["雾"]
    if code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return ["雨"]
    if code in {71, 73, 75, 77, 85, 86}:
        return ["雪"]
    if code in {95, 96, 99}:
        return ["雷", "暴"]
    return ["天气"]


@pytest.mark.live
def test_chat_weather_putian_live_llm() -> None:
    if os.getenv("RUN_LIVE_LLM_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_LLM_TESTS=1 to run live LLM weather integration tests.")

    provider = os.getenv("LIVE_MODEL_PROVIDER", "deepseek")
    provider_config = _parse_provider_from_key_md(provider)
    assert provider_config.get("base_url"), f"{provider} base_url is missing in KEY.md"
    assert provider_config.get("api_key"), f"{provider} api_key is missing in KEY.md"
    assert provider_config.get("model"), f"{provider} model is missing in KEY.md"

    # Force backend config to use KEY.md values for this live integration test.
    os.environ["MODEL_PROVIDER"] = provider
    os.environ["OPENAI_BASE_URL"] = provider_config["base_url"]
    os.environ["OPENAI_API_KEY"] = provider_config["api_key"]
    os.environ["OPENAI_MODEL"] = provider_config["model"]

    import backend.config as config_module

    config_module.get_app_config.cache_clear()
    backend_app = importlib.reload(importlib.import_module("backend.app"))

    # Ensure this test uses KEY.md configuration loaded by backend.
    assert backend_app.config.model.base_url == provider_config["base_url"], "backend is not using KEY.md base_url"
    assert backend_app.config.model.model == provider_config["model"], "backend is not using KEY.md model"
    assert backend_app.config.model.api_key.endswith(provider_config["api_key"][-6:]), "backend is not using KEY.md api_key"
    assert len(backend_app.config.model.api_key) == len(provider_config["api_key"]), "backend api_key length mismatch"

    live_weather = _fetch_live_putian_weather()

    session_id = f"live-putian-{uuid.uuid4().hex[:8]}"
    all_events: list[dict] = []
    final_content = ""
    last_error = ""

    prompts = [
        "今天莆田的天气如何",
        (
            "上一轮未成功。不要调用任何工具，不要函数调用。"
            f"请基于我提供的实时数据直接回答：城市={live_weather.city_name}，"
            f"当前温度={live_weather.temperature_c}℃，weather_code={live_weather.weather_code}。"
            "请回答“今天莆田天气如何”，并包含城市、气温(℃)、天气概述。"
        ),
        (
            f"请复核并只输出结论：今天莆田，当前温度约 {live_weather.temperature_c}℃。"
            "不要调用工具。"
        ),
    ]

    with TestClient(backend_app.app) as client:
        for prompt in prompts:
            response = client.post(
                "/api/chat",
                json={"message": prompt, "session_id": session_id, "stream": False},
            )
            assert response.status_code == 200
            events = response.json()["events"]
            all_events.extend(events)
            error_events = [event for event in events if event.get("type") == "error"]
            if error_events:
                last_error = str(error_events[-1].get("content", "")).strip()

            final_events = [event for event in events if event.get("type") == "final"]
            if not final_events:
                continue
            final_candidate = str(final_events[-1].get("content", "")).strip()
            if not final_candidate:
                continue
            final_content = final_candidate

            temp = _extract_temperature_c(final_content)
            has_city = ("莆田" in final_content) or ("Putian" in final_content)
            if temp is not None and has_city and abs(temp - live_weather.temperature_c) <= 6.0:
                break

    assert all_events, "No events were produced from live chat API."
    assert final_content, f"No final response was produced by the live model. last_error={last_error}"

    assert ("莆田" in final_content) or ("Putian" in final_content), "Final answer does not mention Putian."

    assistant_temp = _extract_temperature_c(final_content)
    assert assistant_temp is not None, f"Final answer does not contain a parseable temperature: {final_content}"

    temp_diff = abs(assistant_temp - live_weather.temperature_c)
    assert temp_diff <= 6.0, (
        f"Temperature drift too large. assistant={assistant_temp}°C, "
        f"live={live_weather.temperature_c}°C, diff={temp_diff}°C"
    )

    expected_keywords = _weather_keywords_from_code(live_weather.weather_code)
    assert any(keyword in final_content for keyword in expected_keywords), (
        f"Final answer weather description seems inconsistent. "
        f"expected one of {expected_keywords}, got: {final_content}"
    )

    session_file = Path("backend/sessions") / f"{session_id}.json"
    if session_file.exists():
        session_file.unlink()
