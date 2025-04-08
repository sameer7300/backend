from django.contrib import admin
from .models import Project, ProjectImage, Skill, Timeline, Resume, Contact

# Register your models here.

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'is_featured', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'is_featured')
    search_fields = ('title', 'description', 'technologies')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectImageInline]
    ordering = ('-created_at',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'proficiency', 'years_experience', 'is_featured')
    list_filter = ('category', 'is_featured')
    search_fields = ('name', 'description')
    ordering = ('category', 'order', '-proficiency')

@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'organization', 'start_date', 'end_date', 'is_current')
    list_filter = ('event_type', 'is_current')
    search_fields = ('title', 'organization', 'description')
    ordering = ('-start_date', 'order')

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['__str__']

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('ip_address', 'user_agent', 'created_at', 'updated_at')
    ordering = ('-created_at',)
