from flask import Flask, render_template, request, jsonify
import os
import requests
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MODEL_NAME = "qwen/qwen2.5-vl-72b-instruct:free"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    """Simple and reliable privacy risk analysis using keyword detection"""
    print("Starting privacy risk analysis...")
    
    if not text or not text.strip():
        return {
            "detected_data": {},
            "risk_level": "low",
            "risk_explanation": "No text detected in the image",
            "recommendations": ["No action needed"]
        }
    
    # Convert text to lowercase for easier matching
    text_lower = text.lower()
    
    # Define keywords for different privacy categories
    personal_identifiers = []
    location_data = []
    financial_info = []
    medical_info = []
    other_sensitive_data = []
    
    # Check for personal identifiers
    personal_keywords = {
        'name': ['name', 'full name', 'first name', 'last name', 'username'],
        'email': ['email', 'e-mail', '@', 'gmail', 'yahoo', 'outlook'],
        'phone': ['phone', 'mobile', 'cell', 'telephone', 'call me', 'contact'],
        'address': ['address', 'street', 'avenue', 'road', 'city', 'zip code', 'postal'],
        'birth': ['birth', 'birthday', 'born', 'age', 'date of birth', 'd.o.b'],
        'id': ['id', 'identification', 'passport', 'driver license', 'license']
    }
    
    for category, keywords in personal_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                personal_identifiers.append(f"Potential {category} information")
                break  # Avoid duplicate entries for same category
    
    # Check for location data
    location_keywords = ['location', 'gps', 'coordinates', 'map', 'here', 'current location', 'latitude', 'longitude']
    for keyword in location_keywords:
        if keyword in text_lower:
            location_data.append(f"Potential {keyword} information")
    
    # Check for financial info
    financial_keywords = {
        'bank': ['bank', 'account number', 'routing number'],
        'card': ['credit card', 'debit card', 'card number', 'expiry', 'cvv'],
        'financial': ['salary', 'income', 'tax', 'ssn', 'social security', 'money']
    }
    
    for category, keywords in financial_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                financial_info.append(f"Potential {category} information")
                break
    
    # Check for medical info
    medical_keywords = ['medical', 'health', 'doctor', 'hospital', 'prescription', 'medicine', 'illness', 'condition']
    for keyword in medical_keywords:
        if keyword in text_lower:
            medical_info.append(f"Potential {keyword} information")
    
    # Check for other sensitive data
    other_keywords = ['password', 'secret', 'confidential', 'private', 'sensitive']
    for keyword in other_keywords:
        if keyword in text_lower:
            other_sensitive_data.append(f"Potential {keyword} information")
    
    # Count total findings
    total_findings = (
        len(personal_identifiers) + 
        len(location_data) + 
        len(financial_info) + 
        len(medical_info) + 
        len(other_sensitive_data)
    )
    
    # Determine risk level
    if total_findings == 0:
        risk_level = "low"
        risk_explanation = "No sensitive information detected in the text"
    elif total_findings <= 2:
        risk_level = "medium"
        risk_explanation = f"Found {total_findings} potential privacy concerns"
    else:
        risk_level = "high"
        risk_explanation = f"Found {total_findings} potential privacy concerns - review carefully"
    
    # Generate recommendations based on risk level
    if risk_level == "low":
        recommendations = [
            "No sensitive information detected",
            "This post appears safe to share"
        ]
    elif risk_level == "medium":
        recommendations = [
            "Review the detected information before sharing",
            "Consider blurring or removing sensitive details",
            "Think about who can see this information"
        ]
    else:  # high risk
        recommendations = [
            "⚠️ High risk detected - reconsider sharing this post",
            "Remove or blur all sensitive information",
            "Consider sharing this content privately instead of publicly",
            "Review privacy settings for your social media accounts"
        ]
    
    # Prepare the result
    result = {
        "detected_data": {
            "personal_identifiers": personal_identifiers,
            "location_data": location_data,
            "financial_info": financial_info,
            "medical_info": medical_info,
            "other_sensitive_data": other_sensitive_data
        },
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
        "recommendations": recommendations
    }
    
    print(f"Privacy analysis completed: {risk_level} risk level")
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        # Create the uploads folder if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
            
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        try:
            # Extract text from image
            print("=== Starting Analysis ===")
            extracted_text = extract_text_from_image(filename)
            
            # Analyze privacy risk
            analysis_result = analyze_privacy_risk(extracted_text)
            
            # Clean up uploaded file
            os.remove(filename)
            
            return jsonify({
                'success': True,
                'extracted_text': extracted_text,
                'analysis': analysis_result
            })
            
        except Exception as e:
            # Clean up file in case of error
            if os.path.exists(filename):
                os.remove(filename)
            print(f"Error in analyze route: {str(e)}")
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)