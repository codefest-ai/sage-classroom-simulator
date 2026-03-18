"""
LLM Client — Stdlib-only interface to local MLX server or Claude API.

Points to http://localhost:8234/v1/chat/completions (MLX default).
Falls back to template-based generation if MLX is down.
No pip dependencies.

Usage:
    from simulator.llm_client import LLMClient
    client = LLMClient()
    response = client.generate("You are a student.", "React to: 'Any questions?'")
"""

import json
import urllib.request
import urllib.error
import os
import time
from typing import Optional, Dict, List


class LLMClient:
    """Minimal LLM client using stdlib urllib."""

    def __init__(
        self,
        base_url: str = "http://localhost:8234/v1/chat/completions",
        model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
        timeout: float = 3.0,
        max_retries: int = 1,
        use_claude: bool = False,
        claude_api_key: Optional[str] = None,
        session_cost_cap: float = 0.50,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_claude = use_claude
        self.claude_api_key = claude_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.session_cost_cap = session_cost_cap
        self._session_cost = 0.0
        self._available = None  # None = unknown, True/False = tested
        self._last_check = 0

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 60,
        temperature: float = 0.8,
    ) -> Optional[str]:
        """
        Generate a completion. Returns None if LLM is unavailable.

        Args:
            system_prompt: Character/context setup
            user_prompt: The actual input to respond to
            max_tokens: Cap response length (keep short for chat simulation)
            temperature: Creativity (0.7-0.9 good for varied student responses)
        """
        if self.use_claude:
            return self._generate_claude(system_prompt, user_prompt, max_tokens, temperature)
        return self._generate_local(system_prompt, user_prompt, max_tokens, temperature)

    def _generate_local(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float,
    ) -> Optional[str]:
        """Generate via local MLX server (OpenAI-compatible API)."""
        # Check availability (cache for 30s)
        if self._available is False and (time.time() - self._last_check) < 30:
            return None

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": ["\n\n"],  # Keep responses single-turn
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    text = result["choices"][0]["message"]["content"].strip()
                    self._available = True
                    self._last_check = time.time()
                    return self._clean_response(text)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                    ConnectionRefusedError, json.JSONDecodeError, KeyError, OSError):
                if attempt == self.max_retries:
                    self._available = False
                    self._last_check = time.time()
                    return None
                time.sleep(0.2)

        return None

    def _generate_claude(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float,
    ) -> Optional[str]:
        """Generate via Claude API (cost-capped)."""
        if not self.claude_api_key:
            return None

        # Cost guard: ~$0.003/1K input tokens, ~$0.015/1K output tokens for Haiku
        estimated_cost = (len(system_prompt + user_prompt) / 4000) * 0.003 + (max_tokens / 1000) * 0.015
        if self._session_cost + estimated_cost > self.session_cost_cap:
            return None  # Cap reached, fall back to templates

        payload = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["content"][0]["text"].strip()
                # Track cost
                usage = result.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                self._session_cost += (input_tokens / 1000) * 0.001 + (output_tokens / 1000) * 0.005
                return self._clean_response(text)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError, KeyError, OSError):
            return None

    def _clean_response(self, text: str) -> str:
        """Post-process LLM output for chat simulation."""
        # Remove AI assistant artifacts
        for prefix in ["Sure!", "Of course!", "As a student,", "I'd say:", "Here's my response:"]:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()

        # Cap at 2 sentences
        sentences = []
        current = ""
        for char in text:
            current += char
            if char in ".!?" and len(current.strip()) > 3:
                sentences.append(current.strip())
                current = ""
                if len(sentences) >= 2:
                    break
        if current.strip() and len(sentences) < 2:
            sentences.append(current.strip())

        result = " ".join(sentences)

        # Length cap
        if len(result) > 200:
            result = result[:197] + "..."

        return result if result else None

    def is_available(self) -> bool:
        """Check if LLM backend is reachable."""
        if self._available is not None and (time.time() - self._last_check) < 30:
            return self._available

        # Quick health check
        try:
            req = urllib.request.Request(
                self.base_url.replace("/chat/completions", "/models"),
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.0):
                self._available = True
        except (urllib.error.URLError, TimeoutError, OSError):
            self._available = False
        self._last_check = time.time()
        return self._available

    @property
    def session_cost(self) -> float:
        """Current session cost in USD (Claude API only)."""
        return round(self._session_cost, 4)
