from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    provider: Literal["anthropic", "openai"] = "anthropic"

    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-6"

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"

    max_file_size_mb: int = 20
    max_pdf_pages: int = 20
    image_render_dpi: int = 150

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def active_model(self) -> str:
        return self.anthropic_model if self.provider == "anthropic" else self.openai_model

    def require_api_key(self) -> str:
        if self.provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when PROVIDER=anthropic")
            return self.anthropic_api_key
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when PROVIDER=openai")
        return self.openai_api_key


settings = Settings()
