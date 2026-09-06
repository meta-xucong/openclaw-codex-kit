---
name: weather-forecast
description: 记录用户明确指定的默认城市，并通过公开天气服务查询当前天气和预报。
---

# 天气预报与城市记忆

这是带本地城市偏好的天气工作流。城市记忆只写入当前项目的本地数据目录，不读取平台配置，
也不保存账号、Cookie 或完整对话历史。实时结果要标注查询时间和来源。

## 首次使用

```powershell
powershell -ExecutionPolicy Bypass -File scripts/weather_db.ps1 has_city
powershell -ExecutionPolicy Bypass -File scripts/weather_db.ps1 set_city "北京"
powershell -ExecutionPolicy Bypass -File scripts/weather_db.ps1 get_city
```

查询公开天气：

```powershell
curl.exe "https://wttr.in/Beijing?format=3"
```

如果需要机器可读的 JSON，可调用 Open-Meteo 等明确配置的公开接口；失败时说明网络或服务状态。

## 存储位置

默认数据文件位于当前工作区的 `codex-data/weather-forecast/`；可用 `WEATHER_DATA_DIR` 指定目录。
不要把该目录中的个人偏好、缓存或运行结果提交到公开仓库。

城市记忆脚本使用 Windows PowerShell 的 JSON 能力，不依赖 Python；天气查询本身仍需要网络。
