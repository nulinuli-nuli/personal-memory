"""AI text parser for natural language input."""
from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.ai.providers import AIProviderFactory
from src.shared.config import settings


class TextParser:
    """Parse natural language text into structured data using AI."""

    def __init__(self, ai_provider=None):
        """
        Initialize the parser with configured AI provider.

        Args:
            ai_provider: Optional AI provider instance (for dependency injection)
        """
        if ai_provider:
            self.ai = ai_provider
        else:
            self.ai = AIProviderFactory.create(
                provider_type=settings.ai_provider,
                api_key=settings.ai_api_key,
                base_url=settings.ai_base_url,
                model=settings.ai_model,
            )
        self.prompts_dir = Path("prompts")

    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from file."""
        prompt_path = self.prompts_dir / prompt_name
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def _format_date(self, date_obj: date) -> str:
        """Format date as YYYY-MM-DD."""
        return date_obj.strftime("%Y-%m-%d")

    def parse_finance(self, text: str, record_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Parse finance-related text.

        Args:
            text: Natural language text describing a finance record
            record_date: Date to use (defaults to today)

        Returns:
            Parsed finance data as dictionary
        """
        if record_date is None:
            record_date = date.today()

        prompt = self._load_prompt("parse_finance.txt")
        formatted_prompt = prompt.format(text=text, today=self._format_date(record_date))

        return self.ai.parse(formatted_prompt, context={})

    def parse_work(self, text: str, record_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Parse work-related text.

        Args:
            text: Natural language text describing a work record
            record_date: Date to use (defaults to today)

        Returns:
            Parsed work data as dictionary
        """
        if record_date is None:
            record_date = date.today()

        prompt = self._load_prompt("parse_work.txt")
        formatted_prompt = prompt.format(text=text, today=self._format_date(record_date))

        return self.ai.parse(formatted_prompt, context={})

    async def chat(self, prompt: str) -> Dict[str, Any]:
        """
        Generic chat method for routing decisions.

        Args:
            prompt: Chat prompt

        Returns:
            AI response as dictionary
        """
        return self.ai.parse(prompt, context={})
