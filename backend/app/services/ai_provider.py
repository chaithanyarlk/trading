"""
Unified AI Provider - Supports both Anthropic Claude and Ollama local LLMs
Routes requests to the configured AI provider
"""
import logging
import json
import requests
from typing import Dict, Optional
import anthropic
from app.core.config import settings

logger = logging.getLogger(__name__)

class UnifiedAIProvider:
    """
    Unified AI provider supporting multiple backends:
    - Anthropic Claude (cloud-based)
    - Ollama (local LLM - Qwen, Llama, etc.)
    """
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.is_anthropic = self.provider == "anthropic"
        self.is_ollama = self.provider == "ollama"
        
        if self.is_anthropic:
            if not settings.CLAUDE_API_KEY:
                logger.warning("⚠️  Claude API key not configured. Switch to Ollama in .env")
            self.client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
            self.model = settings.CLAUDE_MODEL
            logger.info(f"✓ AI Provider: Anthropic Claude ({self.model})")
        elif self.is_ollama:
            self.base_url = settings.OLLAMA_BASE_URL
            self.model = settings.OLLAMA_MODEL
            self._test_ollama_connection()
            logger.info(f"✓ AI Provider: Ollama ({self.model})")
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")
    
    def _test_ollama_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                logger.info(f"  Available models: {', '.join(model_names)}")
                return True
            else:
                logger.error(f"  Ollama returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"  ✗ Cannot connect to Ollama at {self.base_url}")
            logger.info("  Install Ollama from https://ollama.ai and run: ollama serve")
            return False
        except Exception as e:
            logger.error(f"  Error connecting to Ollama: {e}")
            return False
    
    def analyze(self, prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 2000) -> str:
        """
        Send analysis request to configured AI provider
        
        Args:
            prompt: User/system prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum response length
            
        Returns:
            AI response text
        """
        if self.is_anthropic:
            return self._analyze_anthropic(prompt, system_prompt, max_tokens)
        elif self.is_ollama:
            return self._analyze_ollama(prompt, system_prompt, max_tokens)
    
    def _analyze_anthropic(self, prompt: str, system_prompt: Optional[str], max_tokens: int) -> str:
        """Use Anthropic Claude for analysis"""
        try:
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                messages.insert(0, {"role": "user", "content": f"System: {system_prompt}"})
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._fallback_analysis(prompt)
    
    def _analyze_ollama(self, prompt: str, system_prompt: Optional[str], max_tokens: int) -> str:
        """Use Ollama local LLM for analysis"""
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "num_predict": max_tokens,
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama error: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return self._fallback_analysis(prompt)
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out (model might be loading)")
            return self._fallback_analysis(prompt)
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            return self._fallback_analysis(prompt)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._fallback_analysis(prompt)
    
    def _fallback_analysis(self, prompt: str) -> str:
        """Fallback to rule-based analysis when AI unavailable"""
        return "AI service temporarily unavailable. Using fallback rule-based analysis."
    
    def get_provider_info(self) -> Dict:
        """Get current provider configuration"""
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url if self.is_ollama else "N/A"
        }


# Global provider instance
ai_provider = UnifiedAIProvider()
