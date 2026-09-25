from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

# parents[0] = core
# parents[1] = chat_agent
# parents[2] = src
# parents[3] = backend
# parents[4] = Chat-Agent

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[4]
# yaml文件目录
YAML_FILE = PROJECT_ROOT / "backend" / "src" / "chat_agent" /"config" / "config.yaml"
# env文件目录
ENV_FILE = PROJECT_ROOT / ".env"


class DatabaseSettings(BaseModel):
    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chat_agent"
    echo: bool = False
    pool_size: int = Field(default=5, gt=0)
    max_overflow: int = Field(default=10, ge=0)

class AppSettings(BaseModel):
    name: str = "Chat-Agent"
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

class LlmProviderSettings(BaseModel):
    base_url: AnyHttpUrl
    api_key: SecretStr | None = None
    enabled: bool = True

class LlmSettings(BaseModel):
    default_provider: str
    providers: dict[str, LlmProviderSettings]

    # mode = "after"表示：
    # Pydantic先读取原始数据。将字段转换成正确类型。
    # 创建LlmSettings对象。
    # 最后调用validate_default_provider()。
    # 校验成功后返回模型对象。
    @model_validator(mode="after")
    # 类本身没有定义晚，需要添加""作为返回值
    def validate_provider(self) -> "LlmSettings":
        provider = self.providers.get(self.default_provider)
        if provider is None:
            raise ValueError(
                f"default_provider '{self.default_provider}' "
                "不存在于 llm.providers中"
            )
        if not provider.enabled:
            raise ValueError(
                f"default_provider '{self.default_provider}' 已被禁用"
            )
        return self


    def get_provider(
        self,
        name: str | None = None,
    ) -> LlmProviderSettings:
        provider_name = name or self.default_provider

        try:
            provider = self.providers[provider_name]
        except KeyError as exc:
            raise ValueError(f"未知的模型供应商：{provider_name}") from exc

        if not provider.enabled:
            raise ValueError(f"模型供应商已被禁用：{provider_name}")

        return provider





class Settings(BaseSettings):
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LlmSettings

    model_config = SettingsConfigDict(
        yaml_file=YAML_FILE,
        yaml_file_encoding="utf-8",
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        env_prefix="CHAT_AGENT_",
        # env环境变量中的分隔符
        env_nested_delimiter="__",
        # 环境变量名不区分大小写
        case_sensitive=False,
        extra="ignore",
    )

    # 初始化时BaseSettings会自动调用这个方法
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:

        # 返回顺序就是优先级顺序
        return (
            init_settings, # 构造函数
            env_settings, # 操作系统
            dotenv_settings, # env文件
            YamlConfigSettingsSource(settings_cls), # yaml配置
            file_secret_settings,
        )


# 缓存函数执行结果
@lru_cache
def get_settings() -> Settings:
    return Settings()

if __name__ == "__main__":

    settings = get_settings()
    provider = settings.llm.get_provider()

    print("默认供应商：", settings.llm.default_provider)
    print("接口地址：", provider.base_url)
    print("是否启用：", provider.enabled)
    print("API Key 是否存在：", bool(provider.api_key.get_secret_value()))
