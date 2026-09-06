---
name: weather
description: 使用公开天气服务查询指定地点的当前天气、降雨、温度和短期预报。
---

# 天气查询

需要城市、地区、机场代码或经纬度。当前天气是实时信息，必须写明查询时间和数据来源；
涉及预警、航空、海事或官方决策时，优先使用当地官方气象服务。

Windows 可使用系统自带的 `curl.exe`：

```powershell
curl.exe "https://wttr.in/London?format=3"
curl.exe "https://wttr.in/London?format=j1"
```

也可以使用 PowerShell：

```powershell
Invoke-RestMethod "https://wttr.in/Beijing?format=j1"
```

本技能不保存用户位置或查询历史。若需要记忆城市，请由用户明确指定一个项目内的存储文件。
