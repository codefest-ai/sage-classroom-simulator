"""
LLM Client — Stdlib-only interface to Groq (free), Claude API, or local MLX.

Priority: Groq (free, fast) → Claude (paid, best quality) → Local MLX → None

No pip dependencies.

Usage:
    from simulator.llm_client import LLMClient
    client = LLMClient()                    # Auto-detects: Groq if key set, else local MLX
    client = LLMClient(use_groq=True)       # Force Groq (free)
    client = LLMClient(use_claude=True)     # Force Claude Haiku (paid)
    response = client.generate("You are a student.", "React to: 'Any questions?'")
"""

import json
import urllib.request
import urllib.error
import os
import time
from typing import Optional


class LLMClient:
    """Minimal LLM client using stdlib urllib. Supports Groq, Claude, and local MLX."""

    def __init__(
        self,
        base_url: str = "http://localhost:8234/v1/chat/completions",
        model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
        timeout: float = 3.0,
        max_retries: int = 1,
        use_claude: bool = False,
        use_groq: bool = False,
        claude_api_key: Optional[str] = None,
        groq_api_key: Optional[str] = None,
        session_cost_cap: float = 0.50,
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_claude = use_claude
        self.use_groq = use_groq
        self.claude_api_key = claude_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.session_cost_cap = session_cost_cap
        self._session_cost = 0.0
        self._available = None
        self._last_check = 0

        # Auto-detect: prefer Groq (free) if key is available
        if not use_claude and not use_groq and self.groq_api_key:
            self.use_groq = True

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 60,
        temperature: float = 0.8,
    ) -> Optional[str]:
        """Generate a completion. Returns None if LLM is unavailable."""
        if self.use_groq:
            return self._generate_groq(system_prompt, user_prompt, max_tokens, temperature)
        if self.use_claude:
            return self._generate_claude(system_prompt, user_prompt, max_tokens, temperature)
        return self._generate_local(system_prompt, user_prompt, max_tokens, temperature)

    def _generate_groq(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float,
    ) -> Optional[str]:
        """Generate via Groq API (free tier — Llama 3.1 8B)."""
        if not self.groq_api_key:
            return None

        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stop": ["\n\n"],
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.groq_api_key}",
                "User-Agent": "SAGE-Simulator/2.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["choices"][0]["message"]["content"].strip()
                self._available = True
                self._last_check = time.time()
                return self._clean_response(text)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                json.JSONDecodeError, KeyError, OSError):
            return None

    def _generate_local(
        self, system_prompt: str, user_prompt: str,
        max_tokens: int, temperature: float,
    ) -> Optional[str]:
        """Generate via local MLX server (OpenAI-compatible API)."""
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
            "stop": ["\n\n"],
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

        estimated_cost = (len(system_prompt + user_prompt) / 4000) * 0.003 + (max_tokens / 1000) * 0.015
        if self._session_cost + estimated_cost > self.session_cost_cap:
            return None

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
        # Remove model-specific tokens
        for token in ["<|end|>", "<|assistant|>", "<|user|>", "<|system|>", "</s>", "<s>", "[/INST]", "[INST]"]:
            text = text.split(token)[0]
        text = text.strip()

        # Preserve structured JSON outputs for callers that expect machine-readable responses.
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            candidate = text[start:end].strip()
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return candidate
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

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
        if len(result) > 200:
            result = result[:197] + "..."
        return result if result else None

    def is_available(self) -> bool:
        """Check if LLM backend is reachable."""
        if self._available is not None and (time.time() - self._last_check) < 30:
            return self._available

        if self.use_groq:
            self._available = bool(self.groq_api_key)
            self._last_check = time.time()
            return self._available

        if self.use_claude:
            self._available = bool(self.claude_api_key)
            self._last_check = time.time()
            return self._available

        # Local MLX — try /models first, then a minimal completion
        try:
            req = urllib.request.Request(
                self.base_url.replace("/chat/completions", "/models"),
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.0):
                self._available = True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            try:
                payload = json.dumps({"model": self.model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}).encode()
                req = urllib.request.Request(self.base_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=3.0):
                    self._available = True
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
                self._available = False
        self._last_check = time.time()
        return self._available

    @property
    def session_cost(self) -> float:
        """Current session cost in USD (Claude API only; Groq is free)."""
        return round(self._session_cost, 4)

    @property
    def backend_name(self) -> str:
        """Human-readable name of active backend."""
        if self.use_groq:
            return "Groq (Llama 3.1 8B — free)"
        if self.use_claude:
            return "Claude Haiku 4.5"
        return "Local MLX"
