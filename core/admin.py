from django.contrib import admin
from .models import AdminChatMessage, AdminChatThread, ApiConfiguration, BotSubscriptionChannel, DeveloperTask, ExternalApiConnection, IntakeRequest, InternalChat, InternalChatMessage, InternalChatParticipant, InternalContact, Platform, Position, SiteLog, SiteRole, SiteSettings, Station, UserProfile, WebPlatform, WebPlatformFavorite


@admin.register(IntakeRequest)
class IntakeRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "full_name", "pnfl", "company", "department", "position", "phone", "platform", "status")
    list_filter = ("status", "platform", "created_at")
    search_fields = ("full_name", "pnfl", "passport", "phone", "company", "department", "position")
    exclude = ("station",)


admin.site.register(Station)
admin.site.register(Position)
admin.site.register(SiteRole)
admin.site.register(Platform)
admin.site.register(WebPlatform)
admin.site.register(WebPlatformFavorite)
admin.site.register(AdminChatMessage)
admin.site.register(AdminChatThread)
admin.site.register(InternalChat)
admin.site.register(InternalChatParticipant)
admin.site.register(InternalChatMessage)
admin.site.register(InternalContact)
admin.site.register(BotSubscriptionChannel)

admin.site.register(ApiConfiguration)
admin.site.register(ExternalApiConnection)
admin.site.register(DeveloperTask)
admin.site.register(SiteSettings)
admin.site.register(SiteLog)
admin.site.register(UserProfile)
