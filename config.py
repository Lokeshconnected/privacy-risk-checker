import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# File upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Model configuration
MODEL_NAME = "qwen/qwen2.5-vl-72b-instruct:free"

# Analysis prompts
PRIVACY_ANALYSIS_PROMPT = """
Analyze the following text extracted from a social media image for privacy risks. 
Identify and categorize any sensitive personal information found and provide a risk assessment.

Text to analyze: {text}

Please provide your analysis in the following JSON format:
{
    "detected_data": {
        "personal_identifiers": [],
        "location_data": [],
        "financial_info": [],
        "medical_info": [],
        "other_sensitive_data": []
    },
    "risk_level": "low/medium/high",
    "risk_explanation": "Detailed explanation of risks",
    "recommendations": []
}
"""