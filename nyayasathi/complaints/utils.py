import os
from deep_translator import GoogleTranslator
import langid
from difflib import SequenceMatcher

# Language mapping for better language detection
LANGUAGE_MAPPING = {
    'en': 'English',
    'hi': 'Hindi',
    'kn': 'Kannada',
    'ta': 'Tamil',
    'te': 'Telugu',
    'ml': 'Malayalam'
}

def similarity_ratio(text1, text2):
    """
    Calculate similarity ratio between two texts using SequenceMatcher
    Returns a value between 0 and 1, where 1 is identical
    """
    return SequenceMatcher(None, text1.lower().strip(), text2.lower().strip()).ratio()

def check_similar_complaints(user, content, time_window_hours=24, similarity_threshold=0.8):
    """
    Check for similar complaints from the same user within a time window
    Returns the most similar complaint if found, None otherwise
    """
    from datetime import timedelta
    from django.utils import timezone
    from .models import Complaint
    
    # Get complaints from the same user within the time window
    recent_complaints = Complaint.objects.filter(
        user=user,
        submitted_at__gte=timezone.now() - timedelta(hours=time_window_hours)
    )
    
    best_match = None
    best_similarity = 0
    
    for complaint in recent_complaints:
        similarity = similarity_ratio(content, complaint.content)
        if similarity > similarity_threshold and similarity > best_similarity:
            best_similarity = similarity
            best_match = complaint
    
    return best_match, best_similarity

def transcribe_audio(file_path):
    """Transcribe audio file to text"""
    try:
        import whisper
        model = whisper.load_model("tiny")
        result = model.transcribe(file_path)
        return result["text"]
    except Exception as e:
        raise Exception(f"Audio transcription failed: {e}")

def detect_language(text):
    """Detect language of the text"""
    if not text or len(text.strip()) < 3:
        return 'Unknown'
    
    try:
        # Try langid first for better Indian language detection
        langid.set_languages(['en', 'hi', 'kn', 'ta', 'te', 'ml'])
        lid, _ = langid.classify(text)
        
        if lid and lid in LANGUAGE_MAPPING:
            return LANGUAGE_MAPPING[lid]
        
        # Fallback to simple detection
        return 'English'  # Default to English if detection fails
    except Exception:
        return 'Unknown'

def translate_to_english(text, source_lang):
    """Translate text to English if it's not already in English"""
    if source_lang.lower() in ['english', 'en']:
        return text
    
    try:
        # Map full language names to language codes
        lang_code_mapping = {
            'Hindi': 'hi',
            'Kannada': 'kn',
            'Tamil': 'ta',
            'Telugu': 'te',
            'Malayalam': 'ml'
        }
        
        source_code = lang_code_mapping.get(source_lang, source_lang.lower())
        translator = GoogleTranslator(source=source_code, target='en')
        translated = translator.translate(text)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def analyze_complaint_severity(text):
    """Analyze complaint text for emotion, priority, and threat level"""
    text_lower = text.lower()
    
    # Threat keywords
    high_threat_keywords = [
        'kill', 'murder', 'death', 'suicide', 'bomb', 'explosive', 'weapon', 'gun', 'shoot',
        'attack', 'assault', 'rape', 'abuse', 'threat', 'dangerous', 'emergency', 'urgent',
        'immediate', 'help', 'save', 'rescue', 'fire', 'accident', 'hospital', 'ambulance'
    ]
    
    medium_threat_keywords = [
        'harassment', 'bully', 'intimidate', 'scare', 'fear', 'afraid', 'worried', 'concerned',
        'stolen', 'theft', 'robbery', 'fraud', 'cheat', 'scam', 'illegal', 'criminal',
        'police', 'law', 'court', 'legal', 'justice', 'rights', 'violation'
    ]
    
    # Urgency indicators
    urgency_indicators = [
        'now', 'immediately', 'urgent', 'emergency', 'asap', 'quick', 'fast', 'hurry',
        'critical', 'serious', 'important', 'danger', 'risk', 'threat', 'help'
    ]
    
    # Emotion detection
    emotion_keywords = {
        'angry': ['angry', 'furious', 'mad', 'rage', 'hate', 'disgust', 'outrage'],
        'fearful': ['afraid', 'scared', 'fear', 'terrified', 'panic', 'anxiety', 'worried'],
        'sad': ['sad', 'depressed', 'unhappy', 'crying', 'tears', 'grief', 'sorrow'],
        'happy': ['happy', 'joy', 'pleased', 'satisfied', 'content', 'grateful'],
        'neutral': ['neutral', 'normal', 'fine', 'okay', 'alright']
    }
    
    # Find exact keywords present
    found_high_threat = [keyword for keyword in high_threat_keywords if keyword in text_lower]
    found_medium_threat = [keyword for keyword in medium_threat_keywords if keyword in text_lower]
    found_urgency = [indicator for indicator in urgency_indicators if indicator in text_lower]
    
    # Count threat keywords
    high_threat_count = len(found_high_threat)
    medium_threat_count = len(found_medium_threat)
    urgency_count = len(found_urgency)
    
    # Determine threat level
    if high_threat_count > 0:
        threat_level = 'high'
    elif medium_threat_count > 2 or urgency_count > 3:
        threat_level = 'medium'
    else:
        threat_level = 'low'
    
    # Determine priority based on threat level and urgency
    if threat_level == 'high' or urgency_count > 5:
        priority = 'high'
    elif threat_level == 'medium' or urgency_count > 2:
        priority = 'medium'
    else:
        priority = 'low'
    
    # Detect emotion
    emotion_scores = {}
    for emotion, keywords in emotion_keywords.items():
        emotion_scores[emotion] = sum(1 for keyword in keywords if keyword in text_lower)
    
    # Get the emotion with highest score, default to neutral
    detected_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
    if emotion_scores[detected_emotion] == 0:
        detected_emotion = 'neutral'
    
    # Set threat level based on detected emotion if no high/medium threat keywords found
    if threat_level == 'low' and detected_emotion in ['angry', 'fearful']:
        threat_level = 'medium'
    
    # Collect risk factors
    risk_factors = []
    if high_threat_count > 0:
        risk_factors.append('high_threat_keywords')
    if medium_threat_count > 2:
        risk_factors.append('multiple_legal_issues')
    if urgency_count > 3:
        risk_factors.append('high_urgency')
    if detected_emotion in ['angry', 'fearful']:
        risk_factors.append('negative_emotion')
    
    # Add the exact keywords found for display
    exact_keywords = list(set(found_high_threat + found_medium_threat))
    
    # Check if immediate attention is required
    requires_immediate_attention = (
        threat_level == 'high' or 
        urgency_count > 5 or 
        any(keyword in text_lower for keyword in ['emergency', 'immediate', 'urgent', 'help'])
    )
    
    return {
        'emotion': detected_emotion,
        'priority': priority,
        'threat_level': threat_level,
        'risk_factors': risk_factors,
        'requires_immediate_attention': requires_immediate_attention,
        'exact_keywords': exact_keywords
    }