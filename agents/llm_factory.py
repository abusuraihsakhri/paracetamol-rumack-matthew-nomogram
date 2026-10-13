"""
Mock supervisor response provider. No external inference backends are implemented.
"""
from typing import Dict, Any, Optional
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Paracetamol Rumack Matthew Nomogram"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return "Mock response only. No clinical evaluation, guideline verification, or model inference was performed."


class LLMFactory:
    """Creates mock response provider only; unsupported backends raise an error."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Paracetamol Rumack Matthew Nomogram"):
        prov = str(provider).lower()
        if prov in ["mock", "deterministic", "test"]:
            return MockLLM(system_name)
        raise ValueError(f"Unsupported provider '{provider}': only the mock provider is implemented")
