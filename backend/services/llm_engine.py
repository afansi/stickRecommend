import os
import time
from abc import ABC, abstractmethod
import requests

class LLMClient(ABC):
    @abstractmethod
    def analyze_text(self, text: str, prompt: str) -> str:
        pass

class OllamaClient(LLMClient):
    def __init__(self, host: str = "http://ollama:11434", model: str = "llama3.2"):
        self.host = os.getenv("OLLAMA_HOST", host)
        self.model = model

    def analyze_text(self, text: str, prompt: str) -> str:
        # Construct the payload
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\n\nContext:\n{text}",
            "stream": False
        }
        start_time = time.time()
        print(f"🤖 LLM: Sending request to Ollama ({self.model})...")
        try:
            response = requests.post(f"{self.host}/api/generate", json=payload)
            response.raise_for_status()
            duration = time.time() - start_time
            print(f"✅ LLM: Ollama responded in {duration:.2f}s")
            return response.json().get("response", "Error: No response from Ollama")
        except Exception as e:
            print(f"❌ LLM: Ollama request failed after {time.time() - start_time:.2f}s: {e}")
            return f"Error contacting Ollama: {str(e)}"

class CloudClient(LLMClient):
    def __init__(self, api_key: str, provider: str = "openai", model: str = "gpt-4"):
        self.api_key = api_key
        self.provider = provider
        self.model = model
    
    def analyze_text(self, text: str, prompt: str) -> str:
        start_time = time.time()
        print(f"☁️ LLM: Sending request to {self.provider} ({self.model})...")
        provider = self.provider.lower()
        
        res = "Provider not implemented."
        if provider == "openai":
            res = self._call_openai(text, prompt)
        elif provider == "anthropic":
            res = self._call_anthropic(text, prompt)
        elif provider == "gemini":
            res = self._call_gemini(text, prompt)
        elif provider == "deepseek":
            res = self._call_deepseek(text, prompt)
            
        duration = time.time() - start_time
        print(f"✅ LLM: {self.provider} responded in {duration:.2f}s")
        return res

    def _call_openai(self, text: str, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        return self._openai_compatible_request(url, text, prompt, self.model)

    def _call_deepseek(self, text: str, prompt: str) -> str:
        # DeepSeek is OpenAI-compatible
        url = "https://api.deepseek.com/chat/completions"
        # DeepSeek Chat model is usually 'deepseek-chat'
        model = self.model if self.model != "gpt-4" else "deepseek-chat" 
        return self._openai_compatible_request(url, text, prompt, model)

    def _openai_compatible_request(self, url: str, text: str, prompt: str, model:str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a financial analyst expert."},
                {"role": "user", "content": f"{prompt}\n\nContext Input:\n{text}"}
            ],
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error contacting {self.provider}: {str(e)}"

    def _call_anthropic(self, text: str, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        # Map generic model name to Claude if needed
        model = self.model if self.model != "gpt-4" else "claude-3-opus-20240229"
        
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                 {"role": "user", "content": f"{prompt}\n\nContext Input:\n{text}"}
            ]
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
        except Exception as e:
            return f"Error contacting Anthropic: {str(e)}"

    def _call_gemini(self, text: str, prompt: str) -> str:
        # Map model to Gemini
        model = self.model if self.model != "gpt-4" else "gemini-pro"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": f"You are a financial analyst expert.\n{prompt}\n\nContext Input:\n{text}"}]
            }]
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"Error contacting Gemini: {str(e)}"

class LLMFactory:
    @staticmethod
    def get_client(use_cloud: bool = False, api_key: str = None, provider: str = "openai", model: str = "gpt-4") -> LLMClient:
        if use_cloud and api_key:
            return CloudClient(api_key=api_key, provider=provider, model=model)
        # Default to Ollama
        return OllamaClient()
