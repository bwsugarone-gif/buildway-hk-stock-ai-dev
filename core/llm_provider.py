"""
core/llm_provider.py

Provider abstraction for LLM narrative generation.

Architecture rule:
    Python owns all calculations, data processing, financial formulas,
    valuation, DCF, ratios, scoring, and scenarios.

    The LLM is only used for explanation, summaries, risk narrative,
    investment commentary, and report language generation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


SUPPORTED_PROVIDERS = ("deepseek", "claude", "openai")
DEFAULT_PROVIDER = "deepseek"

NARRATIVE_SYSTEM_PROMPT = """
You are an investment report writing assistant.

Strict architecture boundary:
- Do not perform core numerical calculations.
- Do not invent valuations, ratios, scores, prices, percentages, or formulas.
- Use only numeric values supplied by Python in the user message/context.
- Your job is explanation, executive summary, risk narrative, investment
  commentary, and polished report language.
"""


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot be configured or called."""


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None


def _get_secret(key: str, default: str = "") -> str:
    """Read Streamlit secrets first, then environment variables."""
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass

    return os.getenv(key, default)


def get_active_provider(default: str = DEFAULT_PROVIDER) -> str:
    provider = _get_secret("LLM_PROVIDER", default).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        return default
    return provider


def get_provider_config(provider: Optional[str] = None) -> ProviderConfig:
    active = (provider or get_active_provider()).strip().lower()

    if active == "deepseek":
        return ProviderConfig(
            provider="deepseek",
            api_key=_get_secret("DEEPSEEK_API_KEY"),
            base_url=_get_secret("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=_get_secret("DEEPSEEK_MODEL", "deepseek-chat"),
        )

    if active == "claude":
        return ProviderConfig(
            provider="claude",
            api_key=_get_secret("CLAUDE_API_KEY"),
            base_url=_get_secret("CLAUDE_BASE_URL", "https://pro.chr1.com/v1"),
            model=_get_secret("CLAUDE_MODEL", "[m1]claude-sonnet-4-6"),
        )

    if active == "openai":
        return ProviderConfig(
            provider="openai",
            api_key=_get_secret("OPENAI_API_KEY"),
            model=_get_secret("OPENAI_MODEL", "gpt-5"),
        )

    raise LLMProviderError(f"Unsupported LLM provider: {active}")


def _build_client(config: ProviderConfig):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMProviderError(
            "Missing dependency: install the openai package to use LLM providers."
        ) from exc

    if not config.api_key:
        raise LLMProviderError(
            f"Missing API key for provider '{config.provider}'. "
            f"Set it in .env or Streamlit secrets."
        )

    kwargs = {"api_key": config.api_key}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)


def build_messages(
    prompt: str,
    system_prompt: str = NARRATIVE_SYSTEM_PROMPT,
    context: Optional[Dict] = None,
) -> List[Dict[str, str]]:
    """Build chat messages with a fixed no-calculation system boundary."""
    content = prompt
    if context:
        content = (
            "Python-supplied analysis context follows. Treat all numeric values "
            "as already calculated and do not recalculate them.\n\n"
            f"{context}\n\n"
            f"Writing task:\n{prompt}"
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": content},
    ]


class LLMProvider:
    """Switchable OpenAI-compatible provider wrapper with fallback support."""

    def __init__(
        self,
        provider: Optional[str] = None,
        fallback_order: Optional[Sequence[str]] = None,
    ) -> None:
        self.provider = provider or get_active_provider()
        self.fallback_order = list(fallback_order or self._default_fallback_order())

    def _default_fallback_order(self) -> List[str]:
        # Phase 2.0 uses DeepSeek only at runtime. Claude/OpenAI remain configured
        # for future roadmap work and explicit multi-model candidate generation.
        return [self.provider]

    def generate(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        temperature: float = 0.3,
        max_tokens: int = 1200,
        fallback: bool = True,
    ) -> str:
        """Generate narrative text from the active provider."""
        providers = self.fallback_order if fallback else [self.provider]
        errors = []

        for provider in providers:
            try:
                return self._generate_with_provider(
                    provider=provider,
                    prompt=prompt,
                    context=context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as exc:
                errors.append(f"{provider}: {exc}")

        raise LLMProviderError("All LLM providers failed. " + " | ".join(errors))

    def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        context: Optional[Dict],
        temperature: float,
        max_tokens: int,
    ) -> str:
        config = get_provider_config(provider)
        client = _build_client(config)
        response = client.chat.completions.create(
            model=config.model,
            messages=build_messages(prompt=prompt, context=context),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    def generate_candidates(
        self,
        prompt: str,
        providers: Optional[Iterable[str]] = None,
        context: Optional[Dict] = None,
        temperature: float = 0.3,
        max_tokens: int = 1200,
    ) -> Dict[str, str]:
        """
        Future multi-model voting hook.

        Returns one narrative candidate per provider. A later consensus layer can
        compare candidates and select or synthesize the final review.
        """
        selected = list(providers or SUPPORTED_PROVIDERS)
        outputs: Dict[str, str] = {}
        for provider in selected:
            outputs[provider] = self._generate_with_provider(
                provider=provider,
                prompt=prompt,
                context=context,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        return outputs


def generate_llm_narrative(
    prompt: str,
    context: Optional[Dict] = None,
    provider: Optional[str] = None,
) -> str:
    """Convenience helper for report builders and agents."""
    return LLMProvider(provider=provider).generate(prompt=prompt, context=context)
