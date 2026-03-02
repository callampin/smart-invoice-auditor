from src.ai_providers.base import BaseAIProvider
from src.ai_providers.gemini import GeminiProvider
from src.ai_providers.minimax import MiniMaxProvider
from src.ai_providers.openai import OpenAIProvider
from src.config import Config


def get_ai_provider(config: Config) -> BaseAIProvider:
    provider = config.AI_PROVIDER.lower()

    if provider == "gemini":
        return GeminiProvider(config)
    elif provider == "openai":
        return OpenAIProvider(config)
    elif provider == "minimax":
        return MiniMaxProvider(config)
    else:
        raise ValueError(f"Proveedor de IA desconocido: {provider}. Opciones: gemini, openai, minimax")
