import google.generativeai as genai
from django.conf import settings
import json
import re

genai.configure(api_key=settings.GEMINI_API_KEY)


def generate_roadmap(topic):
    model = genai.GenerativeModel('gemini-2.0-flash')

    #promt
    #only json
    prompt = f"""
        Act as a Senior Mentor. Create a learning roadmap for the topic: "{topic}".

        You MUST return ONLY a valid JSON object. Do not add any markdown formatting.
        The JSON structure must be exactly like this:
        {{
            "skills": [
                {{
                    "title": "Skill Name",
                    "category": "Category Name",
                    "difficulty": 1, 
                    "description": "Short description"
                }}
            ],
            "dependencies": [
                {{
                    "from": "Skill Name",
                    "to": "Skill Name",
                    "type": "hard"
                }}
            ]
        }}

        Rules:
        1. 'difficulty' must be integer: 1-4.
        2. 'type' in dependencies must be 'hard' or 'soft'.
        3. Generate exactly 7 to 10 skills.
        4. Ensure dependencies link existing skills.
        5. LANGUAGE RULE: If topic is Ukrainian -> Content in Ukrainian. If English -> English.
        """

    try:
        response = model.generate_content(prompt)
        text = response.text
        text = re.sub(r'```json\n?|```', '', text).strip()
        data = json.loads(text)
        return data

    except Exception as e:
        print(f"Error generating roadmap: {e}")
        return None