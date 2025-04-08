from rest_framework import serializers
from .models import Project, ProjectImage, Skill, Timeline, Resume, Contact

class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectImage
        fields = ['id', 'image', 'caption', 'order']

class ProjectSerializer(serializers.ModelSerializer):
    images = ProjectImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'thumbnail', 'featured_image', 'technologies', 'github_url',
            'live_url', 'status', 'start_date', 'end_date', 'is_featured',
            'order', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'slug', 'short_description', 'thumbnail',
            'technologies', 'status', 'is_featured', 'order'
        ]

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'category', 'icon', 'proficiency',
            'description', 'years_experience', 'is_featured',
            'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class TimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeline
        fields = [
            'id', 'title', 'event_type', 'organization', 'location',
            'description', 'start_date', 'end_date', 'is_current',
            'url', 'icon', 'order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['education', 'experience', 'projects', 'skills']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'subject', 'message',
            'status', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']

class ContactAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'name', 'email', 'subject', 'message', 'status',
            'response', 'ip_address', 'user_agent', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
