from django.contrib import admin
from .models import CustomUser, Complaint

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Complaint)
