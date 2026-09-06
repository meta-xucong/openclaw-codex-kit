---
name: weather
description: Get current weather and forecasts with city memory. Stores user's default location for quick queries.
homepage: https://wttr.in/:help
metadata: {"clawdbot":{"emoji":"🌤️","requires":{"bins":["curl"]}}}
---

# Weather - 天气预报

支持城市记忆功能的天气查询，无需API密钥。

## Workflow

### Step 1: Check Default City

检查用户是否已设置默认城市：

```bash
python3 scripts/weather_db.py has_city
```

If "false", ask user for their city and proceed to Step 2.
If "true", proceed to Step 3.

### Step 2: Set Default City

当用户第一次查询天气或想更改城市时：

```python
from weather_db import set_default_city

# 询问用户所在城市
# "请问你在哪个城市？我会记住它，以后直接查天气。"

set_default_city("北京")
```

### Step 3: Query Weather

使用存储的城市查询天气：

```python
from weather_db import get_default_city

city = get_default_city()
# 使用 wttr.in 查询
```

## wttr.in (primary)

Quick one-liner:
```bash
curl -s "wttr.in/London?format=3"
# Output: London: ⛅️ +8°C
```

Compact format:
```bash
curl -s "wttr.in/London?format=%l:+%c+%t+%h+%w"
# Output: London: ⛅️ +8°C 71% ↙5km/h
```

Full forecast:
```bash
curl -s "wttr.in/London?T"
```

Format codes: `%c` condition · `%t` temp · `%h` humidity · `%w` wind · `%l` location · `%m` moon

Tips:
- URL-encode spaces: `wttr.in/New+York`
- Airport codes: `wttr.in/JFK`
- Units: `?m` (metric) `?u` (USCS)
- Today only: `?1` · Current only: `?0`
- PNG: `curl -s "wttr.in/Berlin.png" -o /tmp/weather.png`

## Open-Meteo (fallback, JSON)

Free, no key, good for programmatic use:
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current_weather=true"
```

Find coordinates for a city, then query. Returns JSON with temp, windspeed, weathercode.

Docs: https://open-meteo.com/en/docs

## Example Interaction

```
User: "今天天气怎么样？"

Claude: [检查是否有默认城市]

# 如果没有存储城市：
"请问你在哪个城市？我会记住它，以后直接说'查天气'就可以了。"

User: "北京"

Claude: [存储城市]
✓ 已记住你在北京

北京: ⛅️ +18°C

# 如果已有存储城市：
北京: ☀️ +22°C 湿度45%
```

## CLI Commands

```bash
# 检查是否有默认城市
python3 scripts/weather_db.py has_city

# 获取默认城市
python3 scripts/weather_db.py get_city

# 设置默认城市
python3 scripts/weather_db.py set_city <city_name>

# 查看完整配置
python3 scripts/weather_db.py get_config
```

## Data Storage

数据存储在用户主目录下的 `.claude/weather_forecast/` 文件夹中：
- Config: `config.json`
- Stores: default_city, unit preference, format preference

*路径示例：*
- macOS/Linux: `~/.claude/weather_forecast/`
- Windows: `%USERPROFILE%\.claude\weather_forecast\`
