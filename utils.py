import requests
import base64
import os
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, MODEL_NAME, PRIVACY_ANALYSIS_PROMPT

def encode_image_to_base64(image_path):
    """Encode image to base64 string"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error encoding image: {str(e)}")

def extract_text_from_image(image_path):
    """Extract text from image using Qwen VL model"""
    print("Starting text extraction from image...")
    
    try:
        base64_image = encode_image_to_base64(image_path)
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image accurately. Return only the extracted text without any additional commentary or analysis."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        print("Sending request to OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        extracted_text = result['choices'][0]['message']['content']
        print("Text extraction completed successfully")
        
        return extracted_text
        
    except Exception as e:
        print(f"Error in extract_text_from_image: {str(e)}")
        raise Exception(f"Failed to extract text from image: {str(e)}")

def analyze_privacy_risk(text):
    """Analyze extracted text for privacy risks"""
    print("Starting privacy risk analysis...")
    
    if not text or not text.strip():
        return {
            "detected_data": {},
            "risk_level": "low",
            "risk_explanation": "No text detected in the image",
            "recommendations": ["No action needed"]
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PRIVACY_ANALYSIS_PROMPT.format(text=text)
                        }
                    ]
                }
            ],
            "max_tokens": 2000
        }
        
        print("Sending analysis request to OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        analysis_text = result['choices'][0]['message']['content']
        print("Privacy analysis completed successfully")
        
        # Try to parse as JSON, but if it fails, return the raw text
        try:
            import json
            return json.loads(analysis_text)
        except json.JSONDecodeError:
            return {
                "detected_data": {"raw_analysis": analysis_text},
                "risk_level": "unknown",
                "risk_explanation": "Analysis completed but could not parse JSON format",
                "recommendations": ["Please review the content manually"]
            }
            
    except Exception as e:
        print(f"Error in analyze_privacy_risk: {str(e)}")
        raise Exception(f"Failed to analyze privacy risk: {str(e)}")