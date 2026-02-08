"""AI provider abstraction layer supporting multiple AI services."""
import json
import sys
import io
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    def parse(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse text and return structured data.

        Args:
            prompt: The prompt to send to the AI
            context: Additional context including schema definition

        Returns:
            Parsed structured data as dictionary
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key, base_url, model)
        self.default_model = model or "gpt-4o-mini"
        self.default_base_url = base_url or "https://api.openai.com/v1"

        # Import here to avoid dependency if not using OpenAI
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=self.default_base_url)

    def parse(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse using OpenAI API with JSON mode."""
        try:
            # Log AI request (truncated for readability)
            prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            print(f"  🤖 调用 AI (OpenAI):", flush=True)
            print(f"    模型: {self.default_model}", flush=True)
            print(f"    提示词: {prompt_preview}", flush=True)

            response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=120.0,  # Increase timeout to 120 seconds
            )
            result = response.choices[0].message.content

            # Log AI response (truncated for readability)
            result_preview = result[:100] + "..." if len(result) > 100 else result
            print(f"    AI 响应: {result_preview}", flush=True)

            # Validate JSON before parsing
            if not result or not result.strip():
                raise ValueError("Empty response from AI")

            # Handle potential markdown code blocks
            result = result.strip()
            if result.startswith("```"):
                # Extract JSON from markdown code block
                lines = result.split("\n")
                if lines[0].startswith("```json"):
                    result = "\n".join(lines[1:])
                elif lines[0].startswith("```"):
                    result = "\n".join(lines[1:])
                # Remove closing code block
                if "```" in result:
                    result = result.split("```")[0].strip()

            parsed = json.loads(result)
            print(f"    解析结果: {parsed}", flush=True)
            return parsed
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse was: {result[:500]}")
        except Exception as e:
            raise Exception(f"API error (OpenAI-compatible): {str(e)}")


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        super().__init__(api_key, base_url, model)
        self.default_model = model or "claude-haiku-4-20250205"

        # Import here to avoid dependency if not using Anthropic
        from anthropic import Anthropic
        # Set default timeout to 120 seconds
        kwargs = {
            "api_key": api_key,
            "timeout": 120.0,
        }
        if base_url:
            kwargs["base_url"] = base_url
        self.client = Anthropic(**kwargs)

    def parse(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse using Anthropic API with tool use."""
        try:
            # Build the tool schema from context
            schema = context.get("schema", {})
            required = context.get("required", [])

            # Log AI request (truncated for readability)
            prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            print(f"  🤖 调用 AI (Anthropic):", flush=True)
            print(f"    模型: {self.default_model}", flush=True)
            print(f"    提示词: {prompt_preview}", flush=True)

            system_prompt = prompt + "\n\nRespond only with a JSON object matching the required schema."

            response = self.client.messages.create(
                model=self.default_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": system_prompt}],
                temperature=0,
            )

            # Extract the content
            content = response.content[0].text

            # Log AI response (truncated for readability)
            content_preview = content[:100] + "..." if len(content) > 100 else content
            print(f"    AI 响应: {content_preview}", flush=True)

            # Validate content before parsing
            if not content or not content.strip():
                raise ValueError("Empty response from AI")

            # Parse JSON from the response
            # Anthropic might wrap JSON in markdown code blocks
            content = content.strip()

            # Handle various markdown formats
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # Find the content between first ``` and next ```
                lines = content.split("\n")
                in_code_block = False
                json_lines = []
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        json_lines.append(line)
                if json_lines:
                    content = "\n".join(json_lines).strip()
                else:
                    # Fallback: just split by ```
                    parts = content.split("```")
                    if len(parts) >= 2:
                        content = parts[1].strip()

            parsed = json.loads(content)
            print(f"    解析结果: {parsed}", flush=True)
            return parsed
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse was: {content[:500]}")
        except Exception as e:
            raise Exception(f"API error (Anthropic-compatible): {str(e)}")


class AIProviderFactory:
    """Factory for creating AI provider instances."""

    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    @classmethod
    def create(cls, provider_type: str, **config) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_type: Type of provider (openai, anthropic)
            **config: Provider configuration (api_key, base_url, model)

        Returns:
            AI provider instance

        Raises:
            ValueError: If provider type is unknown
        """
        provider_class = cls._providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(
                f"Unknown AI provider: {provider_type}. "
                f"Available providers: {list(cls._providers.keys())}"
            )
        return provider_class(**config)

    @classmethod
    def register(cls, name: str, provider_class: type):
        """
        Register a new AI provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from AIProvider)
        """
        if not issubclass(provider_class, AIProvider):
            raise TypeError("Provider class must inherit from AIProvider")
        cls._providers[name.lower()] = provider_class
