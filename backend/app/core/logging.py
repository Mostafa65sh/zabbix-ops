import logging
import sys
from typing import Optional


class ModuleLogFormatter(logging.Formatter):
    """
    Formatter that injects [module=<id>] into log messages.
    """
    def format(self, record: logging.LogRecord) -> str:
        module_tag = getattr(record, "module_id", "core")
        record.module_tag = f"[module={module_tag}]"
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = ModuleLogFormatter(
        "%(asctime)s [%(levelname)s] %(module_tag)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger("zabbix_ops")
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


class ModuleLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically attaches module_id to every log record.
    """
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra["module_id"] = self.extra.get("module_id", "core")
        kwargs["extra"] = extra
        return msg, kwargs


def get_module_logger(module_id: str = "core") -> logging.LoggerAdapter:
    logger = logging.getLogger(f"zabbix_ops.{module_id}")
    return ModuleLoggerAdapter(logger, {"module_id": module_id})
