import datetime
import shutil

from astrbot.api import logger
from astrbot.api.star import Context, Star

from .sync_core import PLUGIN_MODEL_LIST_VERSION, sync_config

KV_KEY_VERSION = "model_list_version"
KV_KEY_LAST_SYNC = "last_sync_at"

_TAG = "[volcplan_sync]"


class VolcplanSyncPlugin(Star):
    """每次重载时按内置清单版本自动同步「火山Plan」命名空间。"""

    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context, config)

    async def initialize(self):
        try:
            last_version = await self.get_kv_data(KV_KEY_VERSION, "")
            if last_version == PLUGIN_MODEL_LIST_VERSION:
                logger.info(
                    "%s 内置清单版本 %s 与上次写入一致，跳过同步",
                    _TAG,
                    PLUGIN_MODEL_LIST_VERSION,
                )
                return

            cfg = self.context.get_config()
            api_key = (getattr(self, "config", None) or {}).get("api_key") or None
            report = sync_config(cfg, api_key)
            if report.skipped:
                logger.error("%s %s", _TAG, report.skipped)
                return

            if report.added or report.updated or report.removed or report.source_created:
                self._backup_config(cfg)
                cfg.save_config()
                key_note = ""
                if report.source_created:
                    key_note = (
                        "，source 新建（key 来源：插件配置）"
                        if report.key_resolved_from == "plugin_config"
                        else "，source 新建（key 为占位值，请在 WebUI 服务商配置中改为真实 Agent Plan API Key）"
                    )
                logger.info(
                    "%s 同步完成：新增 %d 条（%s）、更新 %d 条（%s）、清理 %d 条（%s）%s。请重启 AstrBot 使 provider 生效",
                    _TAG,
                    len(report.added),
                    ", ".join(report.added) or "-",
                    len(report.updated),
                    ", ".join(report.updated) or "-",
                    len(report.removed),
                    ", ".join(report.removed) or "-",
                    key_note,
                )
            else:
                logger.info(
                    "%s 配置已与内置清单 %s 一致，仅回写版本记录",
                    _TAG,
                    PLUGIN_MODEL_LIST_VERSION,
                )

            await self.put_kv_data(KV_KEY_VERSION, PLUGIN_MODEL_LIST_VERSION)
            await self.put_kv_data(
                KV_KEY_LAST_SYNC, datetime.datetime.now().isoformat(timespec="seconds")
            )
        except Exception as e:
            # 同步失败不阻断插件加载，且不回写版本号，下次重载自动重试
            logger.error("%s 同步失败：%r", _TAG, e)

    def _backup_config(self, cfg) -> None:
        src = cfg.config_path
        dst = f"{src}.bak-volcplan-{datetime.date.today():%Y%m%d}"
        shutil.copy2(src, dst)
        logger.info("%s 主配置已备份至 %s", _TAG, dst)
