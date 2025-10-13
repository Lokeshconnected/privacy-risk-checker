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

def generate_risk_scenarios(detected_data, extracted_text):
    """Generate realistic risk scenarios using AI"""
    print("Generating risk scenarios...")
    
    # If no sensitive data found, return basic scenarios
    total_findings = sum(len(items) for items in detected_data.values())
    if total_findings == 0:
        return [
            "✅ No significant risks detected in this post",
            "🔒 This content appears safe for sharing on social media",
            "📱 Continue practicing good privacy habits"
        ]
    
    try:
        # Create a prompt for scenario generation
        scenario_prompt = f"""
        Based on this social media post content and detected sensitive information, generate 3 realistic, specific scenarios of how this information could be misused if shared publicly.

        EXTRACTED TEXT FROM POST:
        {extracted_text[:1000]}

        DETECTED SENSITIVE INFORMATION:
        {json.dumps(detected_data, indent=2)}

        CRITICAL REQUIREMENTS:
        - Generate EXACTLY 3 different scenarios
        - Each scenario must be UNIQUE and focus on DIFFERENT risks
        - Each scenario should be 1-2 sentences long
        - Make them realistic and specific to social media context
        - Focus on concrete consequences (identity theft, stalking, financial fraud, etc.)
        - Use simple, clear language that anyone can understand
        - Start each scenario with a relevant emoji that matches the risk type
        - Format as a numbered list (1., 2., 3.)

        EMOJI GUIDE:
        - 💳 for financial risks
        - 🆔 for identity theft
        - 📍 for location/stalking risks
        - 🏥 for medical privacy risks
        - 🔐 for password/account security
        - 📧 for email/phishing risks
        - 🏠 for home security risks
        - 👤 for impersonation risks

        EXAMPLE FORMAT:
        1. 💳 Someone could use your bank information to make unauthorized purchases or drain your accounts.
        2. 📍 Your location data could help stalkers track your daily routine and know when you're vulnerable.
        3. 🆔 Identity thieves might use your personal details to open credit cards or loans in your name.

        Now generate 3 UNIQUE scenarios for the detected information above:
        """
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": scenario_prompt
                }
            ],
            "max_tokens": 800,
            "temperature": 0.7
        }
        
        print("Sending scenario generation request to OpenRouter API...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        scenarios_text = result['choices'][0]['message']['content']
        
        # Parse the scenarios from the response
        scenarios = []
        for line in scenarios_text.split('\n'):
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or any(char.isdigit() and '.' in line for char in line) or
                        any(emoji in line for emoji in ['🔓', '💳', '👥', '🚨', '📍', '👀', '💰', '🆔', '🏥', '🗺️', '🔐', '📧', '🏦', '🚗', '🏠', '💊', '🔬', '🚶', '📝', '🤖', '📱', '🌐'])):
                # Clean up the scenario text
                scenario = line.lstrip('•- 123.').strip()
                if scenario and len(scenario) > 20:
                    scenarios.append(scenario)
        
        # Remove duplicates
        seen = set()
        unique_scenarios = []
        for scenario in scenarios:
            if scenario not in seen:
                seen.add(scenario)
                unique_scenarios.append(scenario)
        
        # Ensure we have exactly 3 unique scenarios
        while len(unique_scenarios) < 3:
            fallback_scenarios = generate_fallback_scenarios(detected_data)
            for fb_scenario in fallback_scenarios:
                if fb_scenario not in unique_scenarios and len(unique_scenarios) < 3:
                    unique_scenarios.append(fb_scenario)
        
        print("Scenario generation completed successfully")
        return unique_scenarios[:3]
        
    except Exception as e:
        print(f"Error generating scenarios: {str(e)}")
        return generate_fallback_scenarios(detected_data)

def generate_fallback_scenarios(detected_data):
    """Generate fallback scenarios when AI fails"""
    scenarios = []
    
    has_personal = len(detected_data.get('personal_identifiers', [])) > 0
    has_financial = len(detected_data.get('financial_info', [])) > 0
    has_medical = len(detected_data.get('medical_info', [])) > 0
    has_location = len(detected_data.get('location_data', [])) > 0
    has_other = len(detected_data.get('other_sensitive_data', [])) > 0
    
    # Create a pool of unique scenarios based on detected data types
    scenario_pool = []
    
    if has_financial:
        scenario_pool.extend([
            "💳 Scammers could use your financial information to attempt unauthorized transactions or account access.",
            "💰 Fraudsters might impersonate you to gain access to your banking or credit card accounts.",
            "🏦 Your financial details could be used for identity theft to open new accounts in your name."
        ])
    
    if has_personal and has_location:
        scenario_pool.extend([
            "📍 Someone could combine your personal details with location data to track your movements or target your home.",
            "🚗 Criminals might use your address and routine information to plan burglaries when you're away.",
            "🏠 Your location data combined with personal info could enable stalking or physical security threats."
        ])
    elif has_personal:
        scenario_pool.extend([
            "🆔 Identity thieves could use your personal information to open fraudulent accounts or apply for loans.",
            "📧 Your contact details might be used for targeted phishing attacks or spam campaigns.",
            "👤 Scammers could impersonate you to trick your friends and family into sending money."
        ])
    
    if has_medical:
        scenario_pool.extend([
            "🏥 Your medical information could be used for insurance discrimination or targeted health scams.",
            "💊 Fraudsters might use your health data to submit false insurance claims or obtain prescription drugs.",
            "🔬 Your medical conditions could be exploited by companies for targeted advertising or price discrimination."
        ])
    
    if has_location:
        scenario_pool.extend([
            "🗺️ Your location data could be used by stalkers or harassers to track your daily activities.",
            "📍 Businesses might use your location history for unwanted targeted advertising or data brokering.",
            "🚶 Your movement patterns could be analyzed to predict when you're away from home."
        ])
    
    if has_other:
        scenario_pool.extend([
            "🔐 Sensitive information like passwords could be used to compromise your online accounts.",
            "📝 Confidential details might be exposed to competitors or used for corporate espionage.",
            "🚨 Private information could be used for blackmail or extortion attempts."
        ])
    
    # General scenarios as fallbacks
    general_scenarios = [
        "👀 This information could be collected by data brokers and sold to third parties without your consent.",
        "📊 Your personal data might be used to build detailed profiles for manipulative advertising.",
        "🌐 Shared information could be permanently stored online and resurfaced in unexpected contexts."
    ]
    
    # Add general scenarios to the pool
    scenario_pool.extend(general_scenarios)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_scenarios = []
    for scenario in scenario_pool:
        if scenario not in seen:
            seen.add(scenario)
            unique_scenarios.append(scenario)
    
    # Select 3 unique scenarios
    if len(unique_scenarios) >= 3:
        return unique_scenarios[:3]
    else:
        # Fill with additional unique scenarios if needed
        additional_scenarios = [
            "🤖 Automated systems might use your data for training AI models without proper compensation.",
            "📱 Your information could be leaked in future data breaches affecting the platform.",
            "🔒 Even deleted posts can remain in backups and be recovered by determined actors."
        ]
        for scenario in additional_scenarios:
            if scenario not in unique_scenarios and len(unique_scenarios) < 3:
                unique_scenarios.append(scenario)
        return unique_scenarios[:3]

def calculate_privacy_score(total_findings, category_counts):
    """Calculate a privacy score from 0-100"""
    base_score = 100
    
    # Heavy penalties for high-risk categories
    financial_penalty = category_counts['financial'] * 20
    medical_penalty = category_counts['medical'] * 15
    personal_penalty = category_counts['personal'] * 10
    
    # General penalty for any findings
    findings_penalty = total_findings * 5
    
    total_penalty = financial_penalty + medical_penalty + personal_penalty + findings_penalty
    
    final_score = max(0, base_score - total_penalty)
    return final_score

def analyze_privacy_risk(text):
    """Simple and reliable privacy risk analysis using keyword detection"""
    print("Starting privacy risk analysis...")
    
    if not text or not text.strip():
        return {
            "detected_data": {},
            "risk_level": "low",
            "risk_explanation": "No text detected in the image",
            "recommendations": ["No action needed"],
            "privacy_score": 100
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
                personal_identifiers.append(f'Potential {category} information')
                break

    # Check for location data
    location_keywords = ['location', 'gps', 'coordinates', 'map', 'here', 'current location', 'latitude', 'longitude']
    for keyword in location_keywords:
        if keyword in text_lower:
            location_data.append(f'Potential {keyword} information')

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
            medical_info.append(f'Potential {keyword} information')

    # Check for other sensitive data
    other_keywords = ['password', 'secret', 'confidential', 'private', 'sensitive']
    for keyword in other_keywords:
        if keyword in text_lower:
            other_sensitive_data.append(f'Potential {keyword} information')

    # Count total findings
    total_findings = (
        len(personal_identifiers) +
        len(location_data) +
        len(financial_info) +
        len(medical_info) +
        len(other_sensitive_data)
    )

    # Calculate Privacy Score (0-100)
    privacy_score = calculate_privacy_score(total_findings, {
        'personal': len(personal_identifiers),
        'financial': len(financial_info),
        'medical': len(medical_info)
    })

    # Determine risk level based on score
    if privacy_score >= 80:
        risk_level = "low"
    elif privacy_score >= 50:
        risk_level = "medium"
    else:
        risk_level = "high"

    risk_explanation = f"Privacy Score: {privacy_score}/100 - Found {total_findings} potential privacy concerns"

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
    else:
        recommendations = [
            "High risk detected - reconsider sharing this post",
            "Remove or blur all sensitive information",
            "Consider sharing this content privately instead of publicly",
            "Review privacy settings for your social media accounts"
        ]

    # Prepare the detected data
    detected_data = {
        "personal_identifiers": personal_identifiers,
        "location_data": location_data,
        "financial_info": financial_info,
        "medical_info": medical_info,
        "other_sensitive_data": other_sensitive_data
    }

    # Generate risk scenarios
    risk_scenarios = generate_risk_scenarios(detected_data, text)

    # Prepare the final result
    result = {
        "detected_data": detected_data,
        "risk_level": risk_level,
        "risk_explanation": risk_explanation,
        "recommendations": recommendations,
        "privacy_score": privacy_score,
        "total_findings": total_findings,
        "risk_scenarios": risk_scenarios
    }

    print(f"Privacy analysis completed: {risk_level} risk level, Score: {privacy_score}")
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