from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager

# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        email = self.normalize_email(email) if email else ''
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'user')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('user', 'User'),
        ('cop', 'Cop'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='user')
    cop_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    objects = CustomUserManager()
    
    def __str__(self):
        if self.user_type == 'cop':
            return f"Cop {self.cop_id}"
        return f"User {self.username}"

class Complaint(models.Model):
    COMPLAINT_TYPES = [
        ('audio', 'Audio'),
        ('text', 'Text'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    EMOTION_CHOICES = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('angry', 'Angry'),
        ('fearful', 'Fearful'),
        ('neutral', 'Neutral'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('reviewed', 'Reviewed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    complaint_type = models.CharField(max_length=10, choices=COMPLAINT_TYPES, default='text')
    language = models.CharField(max_length=50, blank=True)
    content = models.TextField()
    audio_file = models.FileField(upload_to='audio_complaints/', null=True, blank=True)
    emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='low'
    )
    threat_level = models.CharField(max_length=20, default='low')
    risk_factors = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_complaints')
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original_content = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.priority} - {self.submitted_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-submitted_at']
