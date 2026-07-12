import logging
from typing import List, Dict, Any, Generator
import google.generativeai as genai
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        if self.openai_key:
            openai.api_key = self.openai_key

    def generate_response(
        self,
        prompt: str,
        system_instruction: str = "You are a helpful educational AI assistant.",
        history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generates a text completion.
        """
        # Primary: Groq (llama-3.3-70b-versatile)
        if self.groq_key:
            try:
                import requests
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                if history:
                    for h in history:
                        messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": prompt})

                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.2
                    },
                    timeout=30
                )
                if response.ok:
                    res_json = response.json()
                    return res_json["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Groq API returned error {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Groq generation failed: {str(e)}")

        # Secondary: Gemini
        if self.gemini_key:
            try:
                # Configure system instruction and history if available
                config = {}
                if system_instruction:
                    # system_instruction is passed to Model constructor
                    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
                else:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                
                if history:
                    # Format history to Gemini contents structure: [{"role": "user"/"model", "parts": [str]}]
                    contents = []
                    for h in history:
                        role = "user" if h["role"] == "user" else "model"
                        contents.append({"role": role, "parts": [h["content"]]})
                    contents.append({"role": "user", "parts": [prompt]})
                    response = model.generate_content(contents)
                else:
                    response = model.generate_content(prompt)
                
                return response.text
            except Exception as e:
                logger.error(f"Gemini generation failed: {str(e)}")

        # Secondary: OpenAI
        if self.openai_key:
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                if history:
                    for h in history:
                        messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": prompt})

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI generation failed: {str(e)}")

        # Fallback Mock response
        return self._generate_mock_response(prompt)

    def stream_response(
        self,
        prompt: str,
        system_instruction: str = "You are a helpful educational AI assistant.",
        history: List[Dict[str, str]] = None
    ) -> Generator[str, None, None]:
        """
        Streams a response chunk-by-chunk.
        """
        # Primary: Groq (llama-3.3-70b-versatile)
        if self.groq_key:
            try:
                import requests
                import json
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                if history:
                    for h in history:
                        messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": prompt})

                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": messages,
                        "temperature": 0.2,
                        "stream": True
                    },
                    stream=True,
                    timeout=30
                )
                if response.ok:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    chunk_data = json.loads(data_str)
                                    content = chunk_data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        yield content
                                except Exception:
                                    pass
                    return
                else:
                    logger.error(f"Groq streaming returned error {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Groq streaming failed: {str(e)}")

        # Secondary: Gemini
        if self.gemini_key:
            try:
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
                if history:
                    contents = []
                    for h in history:
                        role = "user" if h["role"] == "user" else "model"
                        contents.append({"role": role, "parts": [h["content"]]})
                    contents.append({"role": "user", "parts": [prompt]})
                    response = model.generate_content(contents, stream=True)
                else:
                    response = model.generate_content(prompt, stream=True)

                for chunk in response:
                    yield chunk.text
                return
            except Exception as e:
                logger.error(f"Gemini streaming failed: {str(e)}")

        # Secondary: OpenAI
        if self.openai_key:
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                if history:
                    for h in history:
                        messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": prompt})

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    stream=True
                )
                for chunk in response:
                    delta = chunk.choices[0].delta
                    if "content" in delta:
                        yield delta["content"]
                return
            except Exception as e:
                logger.error(f"OpenAI streaming failed: {str(e)}")

        # Fallback Mock response streaming
        mock_text = self._generate_mock_response(prompt)
        # Yield mock text in chunks
        chunk_size = 15
        for i in range(0, len(mock_text), chunk_size):
            yield mock_text[i:i + chunk_size]

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Returns rich study-assistant mock answers containing markdown, formulas, and mock citations.
        """
        prompt_lower = prompt.lower()
        if "formula" in prompt_lower or "math" in prompt_lower or "equation" in prompt_lower:
            return (
                "Here is the mathematical explanation you requested.\n\n"
                "### Einstein's Mass-Energy Equivalence\n"
                "The relationship between mass and energy is given by:\n"
                "\\[E = mc^2\\]\n"
                "Where:\n"
                "- \\(E\\) is the kinetic energy.\n"
                "- \\(m\\) is the relativistic mass.\n"
                "- \\(c\\) is the speed of light in a vacuum (\\(\\approx 3 \\times 10^8\\text{ m/s}\\)).\n\n"
                "Let's summarize other classical formulas in a table:\n\n"
                "| Concept | Formula | Unit |\n"
                "| :--- | :--- | :--- |\n"
                "| Newton's Second Law | \\(F = ma\\) | Newton (N) |\n"
                "| Quadratic Formula | \\(x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}\\) | N/A |\n\n"
                "*[Source: Lecture_Notes.pdf, Page 12]*"
            )
        elif "explain" in prompt_lower or "concept" in prompt_lower:
            return (
                "Based on your uploaded study materials, here is a simplified explanation:\n\n"
                "**1. Core Idea**:\n"
                "Retrieval-Augmented Generation (RAG) merges document searches with Large Language Models. Instead of the LLM relying on static training, it queries a vector database (like ChromaDB) for relevant sections and uses them as context to write a grounded answer.\n\n"
                "**2. Key Benefits**:\n"
                "- **No Hallucinations**: Answers are directly anchored to your lecture PDFs.\n"
                "- **Citations**: Automatically shows you exactly which slides or pages the answers are from.\n\n"
                "*[Source: RAG_Tutorial.pdf, Page 3]*"
            )
        else:
            return (
                "Hello! I am your AI Study Assistant. I have analyzed your uploaded materials.\n\n"
                "- I can summarize difficult concepts.\n"
                "- I can generate custom quiz questions and flashcards.\n"
                "- I can help you translate notes or organize your study plan.\n\n"
                "Please upload a document to get started or ask me a specific question!"
            )

llm_service = LLMService()
