from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    CORE_VERSION: str = "0.2.0"
    APP_ENV: str = Field(default="development")
    APP_SECRET: str = Field(default="dev_secret_key_change_in_production")
    HOST: str = Field(default="127.0.0.1")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=False)

    ZABBIX_URL: str = Field(default="http://127.0.0.1/zabbix/api_jsonrpc.php")
    ZABBIX_API_TOKEN: str = Field(default="")
    ZABBIX_ADAPTER_TYPE: str = Field(default="mock")  # 'mock' or 'real'

    DATABASE_URL: str = Field(default="postgresql://zabbix_ops:zabbix_ops@localhost:5432/zabbix_ops")
    CORS_ORIGINS: str = Field(default="http://localhost:5173,http://127.0.0.1:5173")

    MODULES_DIR: Optional[str] = Field(default=None)
    ENABLED_MODULES: str = Field(default="*")
    DISABLED_MODULES: str = Field(default="")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def disabled_modules_list(self) -> List[str]:
        return [m.strip().lower() for m in self.DISABLED_MODULES.split(",") if m.strip()]

    @property
    def resolved_modules_dir(self) -> Path:
        if self.MODULES_DIR:
            return Path(self.MODULES_DIR).resolve()
        # Default: <zabbix-ops-root>/modules
        # config.py is at <root>/backend/app/core/config.py -> parents[3] is <root>
        return (Path(__file__).resolve().parents[3] / "modules").resolve()


settings = Settings()
