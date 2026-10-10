"""火山 Plan 命名空间同步核心逻辑（纯函数，零框架依赖，便于独立测试）。"""

from dataclasses import dataclass, field

PLUGIN_MODEL_LIST_VERSION = "20261010.3"
"""内置清单版本。官方模型阵容变更时：更新 MODEL_LIST 并 bump 此版本号，用户重载插件即自动重新同步。"""

SOURCE_ID = "火山Plan"
API_BASE = "https://ark.cn-beijing.volces.com/api/plan/v3"

# 官方文字模型清单（Agent Plan 个人版「支持模型及 Harness」表格 + 逐模型对 plan 端点实测，2026-10-10）。
# 条目：(model 名, modalities, max_context_tokens)。只收官方清单内实测可用的文字模型，
# 向量化/图片/视频/语音模型不收。
MODEL_LIST = [
    ("doubao-seed-2.0-mini", ["text", "image", "tool_use"], 256000),
    ("doubao-seed-2.1-lite", ["text", "image", "tool_use"], 1024000),
    ("deepseek-v4-flash", ["text", "tool_use"], 1024000),
    ("glm-5.3-flash", ["text", "image", "tool_use"], 1024000),
    ("doubao-seed-2.1-turbo", ["text", "image", "tool_use"], 256000),
    ("doubao-seed-2.1-pro", ["text", "image", "tool_use"], 1024000),
    ("doubao-seed-evolving", ["text", "image", "tool_use"], 1024000),
    ("minimax-m3", ["text", "image", "tool_use"], 1024000),
    ("glm-5.3", ["text", "tool_use"], 1024000),
    ("kimi-k2.7-code", ["text", "image", "tool_use"], 256000),
    ("kimi-k2.8-preview", ["text", "image", "tool_use"], 1024000),
    ("deepseek-v4-pro", ["text", "tool_use"], 1024000),
    ("kimi-k3", ["text", "image", "tool_use"], 1024000),
    ("deepseek-v4.1-flash", ["text", "image", "tool_use"], 1024000),
]

# 清单字段：同步时按此逐字段校正已有条目（enable 除外，保留用户设置）
_SYNC_FIELDS = ("model", "modalities", "custom_extra_body", "max_context_tokens")


@dataclass
class SyncReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    source_created: bool = False
    key_resolved_from: str = ""
    """source 新建时 key 的来源：plugin_config / placeholder / 空"""
    skipped: str = ""
    """非空表示本次未写入及原因。"""

PLACEHOLDER_KEY = "123"
"""创建来源时无可用 key 的占位值，用户之后在 WebUI 服务商配置中改为真实 key。"""


def build_source_entry(api_key: str) -> dict:
    return {
        "provider": "openai",
        "type": "openai_chat_completion",
        "provider_type": "chat_completion",
        "key": [api_key],
        "api_base": API_BASE,
        "timeout": 120,
        "proxy": "",
        "custom_headers": {},
        "id": SOURCE_ID,
        "enable": True,
    }


def build_provider_entry(model: str, modalities: list[str], max_ctx: int) -> dict:
    return {
        "id": f"{SOURCE_ID}/{model}",
        "enable": True,
        "provider_source_id": SOURCE_ID,
        "model": model,
        "modalities": modalities,
        "custom_extra_body": {},
        "max_context_tokens": max_ctx,
    }


def sync_config(cfg: dict, api_key: str | None = None) -> SyncReport:
    """把 cfg 中「火山Plan」命名空间同步为内置清单（原地修改）。

    只增改 provider_sources 中 id 为 SOURCE_ID 的条目与 provider 中
    provider_source_id 为 SOURCE_ID 的条目，用户其他条目零改动。
    """
    report = SyncReport()

    sources = cfg.setdefault("provider_sources", [])
    source = next((s for s in sources if s.get("id") == SOURCE_ID), None)
    if source is None:
        sources.append(build_source_entry(api_key or PLACEHOLDER_KEY))
        report.source_created = True
        report.key_resolved_from = "plugin_config" if api_key else "placeholder"

    expected = {
        f"{SOURCE_ID}/{model}": build_provider_entry(model, mods, max_ctx)
        for model, mods, max_ctx in MODEL_LIST
    }

    providers = cfg.setdefault("provider", [])
    stale: list[dict] = []
    seen: set[str] = set()
    for entry in providers:
        if entry.get("provider_source_id") != SOURCE_ID:
            continue
        pid = entry.get("id")
        exp = expected.get(pid)
        if exp is None:
            stale.append(entry)
            continue
        seen.add(pid)
        diffs = [k for k in _SYNC_FIELDS if entry.get(k) != exp[k]]
        if diffs:
            for k in diffs:
                entry[k] = exp[k]
            report.updated.append(pid)

    for entry in stale:
        providers.remove(entry)
        report.removed.append(entry.get("id", "<unknown>"))

    for pid, exp in expected.items():
        if pid not in seen:
            providers.append(exp)
            report.added.append(pid)

    return report
