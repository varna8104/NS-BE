from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView,
    ComplaintListCreateView, ComplaintDetailView,
    AudioTranscribeView, TextComplaintView,
    DetectLanguageView, CopRegisterView, ComplaintStatusUpdateView,
    echo_content, ChatbotAPIView, summarize_legal_document, ask_legal_document, legal_chatbot
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/cop/register/', CopRegisterView.as_view(), name='cop-register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    
    # Complaint endpoints
    path('complaints/', ComplaintListCreateView.as_view(), name='complaint-list'),
    path('complaints/<int:id>/', ComplaintDetailView.as_view(), name='complaint-detail'),
    path('complaints/<int:complaint_id>/status/', ComplaintStatusUpdateView.as_view(), name='complaint-status-update'),
    path('complaints/audio/', AudioTranscribeView.as_view(), name='audio-complaint'),
    path('complaints/text/', TextComplaintView.as_view(), name='text-complaint'),
    path('complaints/summarize-legal-document/', summarize_legal_document, name='summarize_legal_document'),
    path('complaints/ask-legal-document/', ask_legal_document, name='ask_legal_document'),
    path('complaints/legal-chatbot/', legal_chatbot, name='legal_chatbot'),
    path('detect-language/', DetectLanguageView, name='detect-language'),
    path('echo-content/', echo_content, name='echo-content'),
    path('chatbot/', ChatbotAPIView.as_view(), name='chatbot'),
]
