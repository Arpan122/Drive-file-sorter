from google import genai
from google.genai import types

class Client:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def text_prompt(self, prompt: str) -> str | None:
        response = self.client.models.generate_content(
            model=self.model,
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction="You need to help me sort some files into folders based on their names. Don't say anything like 'Okay, here's what you asked for' or anything like that."
            ),
            contents=[prompt]
        )
        return response.text
    
    def image_prompt(self, image_path: str, prompt: str) -> str | None:
        file = self.client.files.upload(file=image_path)
        response = self.client.models.generate_content(
            model=self.model,
            contents=[file, prompt]
        )
        return response.text