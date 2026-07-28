from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm


from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    model = User

    list_display = (
        "email",
        "full_name",
        "role",
        "xp_total",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "full_name", "google_id")
    ordering = ("-created_at",)
    readonly_fields = ("google_id", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Shaxsiy ma'lumot",
            {"fields": ("full_name", "avatar_url", "google_id")},
        ),
        (
            "Loyihaga oid",
            {"fields": ("role", "region", "target_major", "xp_total")},
        ),
        (
            "Rozilik",
            {"fields": ("consent_share_with_universities", "consent_updated_at")},
        ),
        (
            "Ruxsatlar",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Muhim sanalar",
            {"fields": ("last_login", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )