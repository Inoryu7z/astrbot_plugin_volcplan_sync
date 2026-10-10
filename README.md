[![VolcPlanSync Counter](https://count.getloli.com/get/@Inoryu7z.volcplan_sync?theme=miku)](https://github.com/Inoryu7z/astrbot_plugin_volcplan_sync)

# 🌋 VolcPlanSync · 火山Plan 模型同步

一个火山引擎 Agent Plan 的模型清单自动同步插件。

Agent Plan 端点没有模型列表接口（`GET /api/plan/v3/models` 返回 404），WebUI 的「获取模型列表」按钮在此服务商上不适用，模型条目本只能手动逐条填写——插件把这件事接管下来：每次重载检查一次，把「火山Plan」命名空间同步为内置清单，模型能力数据全部在发版前逐模型实测固化。

---

## ✨ 功能概览

### 🔁 重载即同步

插件每次激活/重载都会比对内置清单版本与上次写入时记录的版本：一致则直接跳过，本次重载不产生任何写入；不一致（含首次运行）才执行同步并回写版本号。

官方模型阵容变更时，插件随发版更新内置清单，重载即完成同步。

### 🧼 清单镜像

同步不是无脑追加，而是让「火山Plan」命名空间严格镜像内置清单：

- 清单里有、配置里没有 → 追加
- 清单里有、配置里也有 → 校正字段（model / modalities / max_context_tokens），`enable` 保留手动设置的开关状态
- 清单里没有、配置里有（官方已下架）→ 清理

### 🛡️ 只动自己的命名空间

只增改「火山Plan」命名空间的条目，其他 provider source 和模型条目一个字节都不会被碰。

写入走 AstrBot 配置持久化接口，BOM/CRLF/缩进由框架原生保持，写前自动备份主配置。

### 📦 内置清单 v1

模型的最大上下文、是否支持图像输入随清单固化进插件。v1 收录 14 个模型（2026-10-10 对火山 plan 端点逐模型实测 HTTP 200），**全部支持工具调用**：

| 模型 | 上下文 | 图像输入 |
|---|---|---|
| doubao-seed-2.0-mini | 256k | ✓ |
| doubao-seed-2.1-lite | 1024k | ✓ |
| deepseek-v4-flash | 1024k | - |
| glm-5.3-flash | 1024k | ✓ |
| doubao-seed-2.1-turbo | 256k | ✓ |
| doubao-seed-2.1-pro | 1024k | ✓ |
| doubao-seed-evolving | 1024k | ✓ |
| minimax-m3 | 1024k | ✓ |
| glm-5.3 | 1024k | - |
| kimi-k2.7-code | 256k | ✓ |
| kimi-k2.8-preview | 1024k | ✓ |
| deepseek-v4-pro | 1024k | - |
| kimi-k3 | 1024k | ✓ |
| deepseek-v4.1-flash | 1024k | ✓ |

---

## ⚙️ 主要配置项

| 配置 | 说明 |
|------|------|
| `api_key` | 火山引擎 Agent Plan 的 API Key（`ark-` 开头），可选。配置中不存在「火山Plan」来源时，填了就随来源一起写入；不填则来源照常创建、key 使用占位值，之后在 WebUI 服务商配置中改为真实 key 即可；来源已存在则不读取、不覆盖 |

## 📝 使用说明

1. 安装插件后重载：配置中自动写入「火山Plan」来源与 14 个模型条目；未填 `api_key` 时来源的 key 为占位值。
2. 在 WebUI 服务商配置中把「火山Plan」的 key 改为真实 Agent Plan API Key（`ark-` 开头），保存。
3. 重启 AstrBot，provider 生效。
4. 之后重载插件，清单版本没变就不会有任何写入；官方模型阵容变更随插件发版生效。
