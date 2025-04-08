from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=200)
    thumbnail = models.ImageField(upload_to='projects/thumbnails/')
    featured_image = models.ImageField(upload_to='projects/featured/')
    technologies = models.JSONField(default=list)
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']

    def __str__(self):
        return self.title

class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.project.title} - Image {self.order}"

class Skill(models.Model):
    class Category(models.TextChoices):
        FRONTEND = 'frontend', _('Frontend')
        BACKEND = 'backend', _('Backend')
        DATABASE = 'database', _('Database')
        DEVOPS = 'devops', _('DevOps')
        TOOLS = 'tools', _('Tools')
        OTHER = 'other', _('Other')

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    icon = models.FileField(upload_to='skills/icons/', blank=True)
    proficiency = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    description = models.TextField(blank=True)
    years_experience = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0)]
    )
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order', '-proficiency']
        unique_together = ['name', 'category']

    def __str__(self):
        return f"{self.name} ({self.category})"

class Timeline(models.Model):
    class EventType(models.TextChoices):
        EDUCATION = 'education', _('Education')
        WORK = 'work', _('Work Experience')
        PROJECT = 'project', _('Project')
        ACHIEVEMENT = 'achievement', _('Achievement')
        OTHER = 'other', _('Other')

    title = models.CharField(max_length=200)
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.OTHER
    )
    organization = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    url = models.URLField(blank=True)
    icon = models.FileField(upload_to='timeline/icons/', blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'order']

    def __str__(self):
        return f"{self.title} at {self.organization}"

class Resume(models.Model):
    education = models.JSONField(default=list)
    experience = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    
    class Meta:
        verbose_name = 'Resume'
        verbose_name_plural = 'Resume'

    def __str__(self):
        return 'Resume'

class Contact(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        ARCHIVED = 'archived', _('Archived')

    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    response = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
