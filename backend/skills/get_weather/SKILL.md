---
name: get_weather
description: 获取指定城市天气，优先使用公开天气 API 并返回结构化结果
---

## 触发条件

- 用户明确询问天气、温度、降水、风力等。
- 用户提供城市名（若未提供，先追问）。

## 执行步骤

1. 使用 `fetch_url` 请求天气 API（示例：Open-Meteo geocoding + forecast）。
2. 如果需要数据清洗，可用 `python_repl` 解析 JSON。
3. 若 API 不可用，使用 `terminal` + `curl` 作为备选。
4. 输出前校验单位（摄氏度、降水概率）。

## 输出格式

- 城市与时间
- 当前温度 / 体感
- 天气概述
- 未来 24 小时关键变化
- 数据来源 URL
