from openai import OpenAI

from ...core.config import settings


def get_openai_client() -> OpenAI:
    provider = settings.llm_provider.lower()

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured.")
        return OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        client_kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url
        return OpenAI(**client_kwargs)

    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
