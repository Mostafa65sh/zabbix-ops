from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
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

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
