from django.contrib import admin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'status', 'email_verified', 'is_staff')
    list_filter = ('role', 'status', 'email_verified', 'is_staff')
    search_fields = ('email',)
