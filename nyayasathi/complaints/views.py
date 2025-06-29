import os
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from .utils import (
    transcribe_audio, detect_language, translate_to_english,
    analyze_complaint_severity, LANGUAGE_MAPPING, check_similar_complaints
)
from .models import Complaint, CustomUser
from .serializers import ComplaintSerializer, UserSerializer, LoginSerializer, CopSerializer, ComplaintStatusSerializer
from rest_framework.decorators import api_view, permission_classes, parser_classes
from deep_translator import GoogleTranslator
import langid
from datetime import datetime, timedelta
from django.utils import timezone
import requests
from groq import Groq
import pdfplumber
import docx
from rest_framework.parsers import JSONParser

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
HUGGINGFACE_WHISPER_MODEL = "distil-whisper-large-v3-en"

class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'User registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CopRegisterView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CopSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Cop registered successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get('user')
            if not user:
                return Response({'error': 'User not found in validated data'}, status=status.HTTP_400_BAD_REQUEST)
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'message': 'Login successful'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            request.user.auth_token.delete()
            logout(request)
            return Response({'message': 'Logout successful'})
        except:
            return Response({'message': 'Logout successful'})

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class ComplaintListCreateView(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.user_type == 'cop':
            return Complaint.objects.all()
        return Complaint.objects.filter(user=self.request.user)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        # Add original_content for non-English complaints
        for i, obj in enumerate(queryset):
            if hasattr(obj, 'language') and obj.language and obj.language != 'en':
                data[i]['original_content'] = obj.content if hasattr(obj, 'original_content') else ''
        return Response(data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ComplaintDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def get_queryset(self):
        if self.request.user.user_type == 'cop':
            return Complaint.objects.all()
        return Complaint.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        if hasattr(instance, 'language') and instance.language and instance.language != 'en':
            data['original_content'] = instance.content if hasattr(instance, 'original_content') else ''
        return Response(data)

class ComplaintStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        if request.user.user_type != 'cop':
            return Response({'error': 'Only cops can update complaint status'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            complaint = Complaint.objects.get(id=complaint_id)
        except Complaint.DoesNotExist:
            return Response({'error': 'Complaint not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ComplaintStatusSerializer(data=request.data)
        if serializer.is_valid():
            complaint.status = serializer.validated_data['status']
            complaint.review_notes = serializer.validated_data.get('review_notes', '')
            complaint.reviewed_by = request.user
            complaint.save()
            
            return Response({
                'message': 'Complaint status updated successfully',
                'complaint': ComplaintSerializer(complaint).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AudioTranscribeView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        audio_file = request.FILES.get('audio')
        if not audio_file:
            return Response({'error': 'No audio file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if API key is configured
        if not GROQ_API_KEY:
            return Response({
                'error': 'Groq API key is not configured. Please set GROQ_API_KEY in your .env file.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Use Groq for transcription
        try:
            client = Groq(api_key=GROQ_API_KEY)
            # Save the uploaded file to a temporary location
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp:
                for chunk in audio_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as file:
                transcription = client.audio.transcriptions.create(
                    file=(audio_file.name, file.read()),
                    model="distil-whisper-large-v3-en",
                    response_format="verbose_json",
                )
            transcript = transcription.text
        except Exception as e:
            return Response({'error': f'Groq API transcription failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Detect language
        lang, confidence = langid.classify(transcript)
        detected_language = lang
        translated_text = transcript
        # Translate to English if needed
        if lang != 'en':
            try:
                translated_text = GoogleTranslator(source='auto', target='en').translate(transcript)
            except Exception as e:
                return Response({'error': f'Translation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Check for duplicate complaints from the same user within last 24 hours
        existing_complaint, similarity_score = check_similar_complaints(
            request.user, translated_text, time_window_hours=24, similarity_threshold=0.8
        )
        
        if existing_complaint:
            return Response({
                "error": f"A similar complaint has already been submitted (similarity: {similarity_score:.1%}). Please check your existing complaints or wait before submitting again.",
                "duplicate_complaint_id": existing_complaint.id,
                "similarity_score": similarity_score
            }, status=status.HTTP_400_BAD_REQUEST)

        # 3. Enhanced analysis with threat detection
        analysis = analyze_complaint_severity(translated_text)
        emotion = analysis['emotion']
        priority = analysis['priority']
        threat_level = analysis['threat_level']
        risk_factors = analysis['risk_factors']
        exact_keywords = analysis.get('exact_keywords', [])

        # Debug logging
        print('LANG:', lang)
        print('ORIGINAL CONTENT TO SAVE:', transcript)
        # 4. Save complaint
        complaint = Complaint.objects.create(
            user=request.user,
            name="Anonymous",
            location="Unknown",
            complaint_type='audio',
            language=lang,
            content=translated_text,
            original_content=transcript,  # Always save the transcribed text
            audio_file=audio_file,
            emotion=emotion,
            priority=priority,
            threat_level=threat_level,
            risk_factors=risk_factors
        )

        return Response({
            'transcript': transcript,
            'detected_language': detected_language,
            'translated_text': translated_text,
            'emotion': emotion,
            'priority': priority,
            'threat_level': threat_level,
            'risk_factors': risk_factors,
            'exact_keywords': exact_keywords,
            'requires_immediate_attention': analysis['requires_immediate_attention'],
            'complaint_id': complaint.id
        }, status=status.HTTP_200_OK)

class TextComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.user_type != 'user':
            return Response({"error": "Only users can submit complaints"}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            name = request.data.get("name")
            location = request.data.get("location")
            content = request.data.get("content")

            if not all([name, location, content]):
                return Response({"error": "Name, location, and content are required"}, status=400)

            # Detect language and translate if needed
            lang = detect_language(content)
            translated = translate_to_english(content, lang)

            # Check for duplicate complaints from the same user within last 24 hours
            existing_complaint, similarity_score = check_similar_complaints(
                request.user, translated, time_window_hours=24, similarity_threshold=0.8
            )
            
            if existing_complaint:
                return Response({
                    "error": f"A similar complaint has already been submitted (similarity: {similarity_score:.1%}). Please check your existing complaints or wait before submitting again.",
                    "duplicate_complaint_id": existing_complaint.id,
                    "similarity_score": similarity_score
                }, status=status.HTTP_400_BAD_REQUEST)

            # Enhanced analysis with threat detection
            analysis = analyze_complaint_severity(translated)
            emotion = analysis['emotion']
            priority = analysis['priority']
            threat_level = analysis['threat_level']
            risk_factors = analysis['risk_factors']
            exact_keywords = analysis.get('exact_keywords', [])

            # Debug logging
            print('LANG:', lang)
            print('ORIGINAL CONTENT TO SAVE:', content)
            # Save complaint
            complaint = Complaint.objects.create(
                user=request.user,
                name=name,
                location=location,
                complaint_type='text',
                language=lang,
                content=translated,
                original_content=content,  # Always save the user's input
                emotion=emotion,
                priority=priority,
                threat_level=threat_level,
                risk_factors=risk_factors
            )

            # Add original_content to response if not English
            response_data = {
                "message": "Text complaint submitted successfully",
                "complaint_id": complaint.id,
                "language": lang,
                "emotion": emotion,
                "priority": priority,
                "threat_level": threat_level,
                "risk_factors": risk_factors,
                "exact_keywords": exact_keywords,
                "requires_immediate_attention": analysis['requires_immediate_attention'],
                "content": translated
            }
            if lang != 'en':
                response_data["original_content"] = content

            return Response(response_data)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def DetectLanguageView(request):
    text = request.data.get('text', '')
    if not text or len(text.strip()) < 3:
        return Response({'language': 'Unknown'})
    try:
        lang = detect_language(text)
        if lang and lang != 'Unknown' and lang != 'English':
            return Response({'language': lang})
        # Fallback: try langid
        try:
            langid.set_languages(['en', 'hi', 'kn', 'ta', 'te', 'ml'])  # English, Hindi, Kannada, Tamil, Telugu, Malayalam
            lid, _ = langid.classify(text)
            if lid and lid != 'en':
                # Convert langid result to full language name
                full_lang = LANGUAGE_MAPPING.get(lid, lid.title())
                return Response({'language': full_lang})
        except Exception:
            pass
        return Response({'language': lang if lang else 'Unknown'})
    except Exception:
        return Response({'language': 'Unknown'})

@api_view(['POST'])
@permission_classes([AllowAny])
def echo_content(request):
    return Response({'received': request.data.get('content', '')})

class ChatbotAPIView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        user_message = request.data.get('message', '')
        document = request.FILES.get('document')
        context = (
            "You are a legal assistant for Nyayasathi. "
            "Help users with legal questions, complaint submission, status tracking, and provide IPC-based solutions. "
            "If a legal document is provided, summarize it and suggest solutions as per the Indian Penal Code (IPC). "
            "If the user wants to submit a complaint or check status, guide them and ask for required details."
        )

        if document:
            try:
                text = document.read().decode('utf-8')
            except Exception:
                text = '[Could not read document. Please upload a plain text file.]'
            user_message += f"\n\nHere is a legal document. Summarize it and suggest solutions as per IPC:\n{text}"

        payload = {
            "model": "llama-3-70b-8192",
            "messages": [
                {"role": "system", "content": context},
                {"role": "user", "content": user_message}
            ]
        }
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        groq_response = requests.post(GROQ_API_URL, json=payload, headers=headers)
        try:
            answer = groq_response.json()['choices'][0]['message']['content']
        except Exception:
            answer = "Sorry, I couldn't process your request. Please try again."
        return Response({"answer": answer})

@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
def summarize_legal_document(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if API key is configured
    if not GROQ_API_KEY:
        return Response({
            'error': 'Groq API key is not configured. Please set GROQ_API_KEY in your .env file.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Extract text based on file type
    ext = os.path.splitext(file.name)[1].lower()
    text = ''
    try:
        if ext == '.pdf':
            with pdfplumber.open(file) as pdf:
                text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        elif ext in ['.docx', '.doc']:
            doc = docx.Document(file)
            text = '\n'.join([para.text for para in doc.paragraphs])
        elif ext in ['.txt']:
            text = file.read().decode('utf-8')
        else:
            return Response({'error': 'Unsupported file type.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Failed to extract text: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if not text.strip():
        return Response({'error': 'No text found in the document.'}, status=status.HTTP_400_BAD_REQUEST)

    # Use Groq API for Llama-3.1-8b-instant
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"Summarize the following legal document and extract key information such as parties involved, dates, case numbers, and main issues.\n\nDocument:\n{text}"
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        summary = completion.choices[0].message.content
        return Response({'summary': summary}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'LLM API request failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def ask_legal_document(request):
    document_text = request.data.get('document_text', '')
    question = request.data.get('question', '')
    if not document_text or not question:
        return Response({'error': 'Both document_text and question are required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if API key is configured
    if not GROQ_API_KEY:
        return Response({
            'error': 'Groq API key is not configured. Please set GROQ_API_KEY in your .env file.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"Given the following legal document, answer the user's question as accurately as possible.\n\nDocument:\n{document_text}\n\nQuestion: {question}\n\nAnswer:"
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        answer = completion.choices[0].message.content
        return Response({'answer': answer}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'LLM API request failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser])
def legal_chatbot(request):
    question = request.data.get('question', '')
    model = request.data.get('model', 'llama-3.1-8b-instant')
    if not question:
        return Response({'error': 'Question is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if API key is configured
    if not GROQ_API_KEY:
        return Response({
            'error': 'Groq API key is not configured. Please set GROQ_API_KEY in your .env file.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Supported models for Groq
    supported_models = [
        'llama-3.1-8b-instant',
        'llama-3-8b-8192',
        'llama-3-70b-8192',
        'llama-3.3-70b-versatile',
        'gpt-3.5-turbo',
        'deepseek-chat',
    ]
    # Map friendly names to Groq model IDs if needed
    model_map = {
        'llama': 'llama-3.1-8b-instant',
        'chatgpt': 'gpt-3.5-turbo',
        'deepseek': 'deepseek-chat',
    }
    model_id = model_map.get(model.lower(), model)
    if model_id not in supported_models:
        model_id = 'llama-3.1-8b-instant'
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"You are a helpful legal assistant. Answer the user's question as accurately as possible.\n\nQuestion: {question}\n\nAnswer:"
    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=512,
            top_p=1,
            stream=False,
        )
        answer = completion.choices[0].message.content
        return Response({'answer': answer}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': f'LLM API request failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


