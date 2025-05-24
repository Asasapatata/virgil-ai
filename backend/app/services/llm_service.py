from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
import anthropic
import httpx
from app.core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content

class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            messages=[{"role": "user", "content": full_prompt}]
        )
        
        return response.content[0].text

class DeepSeekProvider(LLMProvider):
    def __init__(self):
        self.base_url = settings.DEEPSEEK_URL  # RunPod endpoint
        self.api_key = settings.DEEPSEEK_API_KEY
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        async with httpx.AsyncClient() as client:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "deepseek-coder",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

class LLMService:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "deepseek": DeepSeekProvider()
        }
    
    async def generate(self, 
                      provider: str, 
                      prompt: str, 
                      system_prompt: Optional[str] = None) -> str:
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        llm = self.providers[provider]
        return await llm.generate(prompt, system_prompt)
    
    # AGGIUNGI QUESTO METODO per compatibilità con CodeGenerator
    async def generate_text(self, prompt: str, provider: str = "anthropic") -> str:
        """Wrapper method for compatibility with CodeGenerator"""
        return await self.generate(provider=provider, prompt=prompt)