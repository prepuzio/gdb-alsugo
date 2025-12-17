import os
import requests

def _post_req_ai(url, api_key, payload):
    headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
            }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()
    else:
        raise Exception(f"HTTP {res.status_code}: {res.text!r}")

class AiClient:
    def __init__(self, provider=None):
        self.providers = {
            "apiyi": self._apiyi_query,
            "openai": self._openai_query
            }
        self.api_keys = {}

        for key in self.providers.keys():
            self.api_keys[key] = os.getenv(f"{key.upper()}_API_KEY")
        
        if provider is not None:
            self.provider = provider
            if self.provider not in self.providers:
                raise ValueError(f"unsupported provider: {provider}")
        else:
            self.provider = self.guess_provider()
            if self.provider is None:
                raise ValueError(f"please provide a valid api key")

    def query(self, prompt: str) -> str:
        return self.providers[self.provider](prompt)["choices"][0]["message"]["content"]

    def guess_provider(self):
        return next((k for k, v in self.api_keys.items() if v not in ('', None)), None)


    def _openai_query(self, prompt: str):
        api_key = self.api_keys["openai"]
        payload = {
            "model": "gpt-4.1-mini",
            "input": f"{prompt}"
        }
        return _post_req_ai(
                url="https://api.openai.com/v1/responses",
                payload=payload,
                api_key=api_key)["output"][0]["content"][0]["text"]

    def _apiyi_query(self, prompt: str) -> str:
        api_key = self.api_keys["apiyi"]
        payload = {
                "model": "gpt-4o-mini",
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}"
                    }
                ]
        }
        return _post_req_ai(
                url="https://api.apiyi.com/v1/chat/completions",
                payload=payload,
                api_key=api_key)#['choices'][0]['message']['content']
