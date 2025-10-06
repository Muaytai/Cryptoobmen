from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, UserDocument


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'kyc_verified', 'is_staff')
    list_filter = ('is_verified', 'kyc_verified', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number', 'avatar', 'telegram_id')}),
        (_('KYC info'), {'fields': ('kyc_verified', 'full_name', 'date_of_birth', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 
                                      'groups', 'user_permissions')}),
        (_('Security'), {'fields': ()}),
        (_('Notifications'), {'fields': ('notify_via_email', 'notify_via_telegram')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_login_ip')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )
    ordering = ('email',)


class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'status', 'uploaded_at')
    list_filter = ('document_type', 'status')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('uploaded_at',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('user', 'document_type', 'document_file')
        return self.readonly_fields


admin.site.register(User, CustomUserAdmin)
admin.site.register(UserDocument, UserDocumentAdmin)
