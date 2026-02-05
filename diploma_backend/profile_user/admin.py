from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = 'pk', 'full_name', 'email', 'phone'
    list_display_links = 'pk', 'full_name'
    ordering = 'pk',
