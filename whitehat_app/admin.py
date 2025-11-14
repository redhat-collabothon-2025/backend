from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from whitehat_app.models import User, Campaign, Event, Incident, RiskHistory


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'name')

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'name', 'risk_score', 'risk_level', 'is_active', 'is_staff')


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('email', 'name', 'risk_level', 'risk_score', 'is_staff')
    list_filter = ('risk_level', 'is_staff', 'is_superuser')
    ordering = ('email',)
    search_fields = ('email', 'name')

    fieldsets = (
        ('User Info', {'fields': ('email', 'name', 'password')}),
        ('Risk', {'fields': ('risk_score', 'risk_level')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        ('New User', {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2')
        }),
    )


admin.site.register(User, UserAdmin)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('persona_name', 'scenario', 'status', 'sent_at', 'target_count', 'click_count')
    search_fields = ('persona_name', 'scenario')
    list_filter = ('status',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'created_at')
    list_filter = ('event_type',)
    search_fields = ('user__email',)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('user', 'incident_type', 'severity', 'created_at')
    list_filter = ('severity',)
    search_fields = ('user__email',)


@admin.register(RiskHistory)
class RiskHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'risk_score', 'created_at')
    search_fields = ('user__email',)
