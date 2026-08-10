from django.contrib import admin

from .models import BookingRequest, LSAProfile, Parent


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "child_name", "created_at"]
    search_fields = ["full_name", "email", "child_name"]


@admin.register(LSAProfile)
class LSAProfileAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "status", "hourly_rate"]
    list_filter = ["status"]
    search_fields = ["full_name", "email"]


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ["id", "parent", "lsa", "session_start", "session_end", "status"]
    list_filter = ["status"]
    autocomplete_fields = ["parent", "lsa"]