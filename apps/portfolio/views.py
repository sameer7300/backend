from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    Project,
    ProjectImage,
    Skill,
    Timeline,
    Resume,
    Contact,
)
from .serializers import (
    ProjectSerializer,
    ProjectListSerializer,
    ProjectImageSerializer,
    SkillSerializer,
    TimelineSerializer,
    ResumeSerializer,
    ContactSerializer,
    ContactAdminSerializer,
)
from apps.accounts.permissions import IsAdmin

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer

    def get_queryset(self):
        queryset = Project.objects.all()
        if self.action == 'list':
            status = self.request.query_params.get('status', 'published')
            if status == 'all' and self.request.user.is_staff:
                return queryset
            return queryset.filter(status=status)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def upload_images(self, request, slug=None):
        project = self.get_object()
        files = request.FILES.getlist('images')
        order = ProjectImage.objects.filter(project=project).count()
        
        images = []
        for file in files:
            image = ProjectImage.objects.create(
                project=project,
                image=file,
                order=order
            )
            order += 1
            images.append(image)
        
        serializer = ProjectImageSerializer(images, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Skill.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

class TimelineViewSet(viewsets.ModelViewSet):
    queryset = Timeline.objects.all()
    serializer_class = TimelineSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Timeline.objects.all()
        event_type = self.request.query_params.get('type', None)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        return queryset

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        # Always return the first resume or create one if none exists
        resume, created = Resume.objects.get_or_create(pk=1, defaults={
            'education': [
                {
                    'school': 'Example University',
                    'degree': 'Bachelor of Science',
                    'field': 'Computer Science',
                    'startDate': '2019',
                    'endDate': '2023',
                    'description': 'Graduated with honors, focused on software engineering and artificial intelligence.',
                    'gpa': '3.8'
                }
            ],
            'experience': [
                {
                    'company': 'Tech Corp',
                    'position': 'Software Engineer',
                    'startDate': '2023',
                    'endDate': 'Present',
                    'description': 'Full-stack development using modern technologies.',
                    'achievements': [
                        'Developed and maintained multiple web applications',
                        'Improved system performance by 40%',
                        'Led a team of 3 developers'
                    ],
                    'technologies': ['React', 'Django', 'PostgreSQL', 'Docker']
                }
            ],
            'projects': [
                {
                    'name': 'Portfolio Website',
                    'description': 'Personal portfolio website built with React and Django',
                    'technologies': ['React', 'Django', 'Tailwind CSS', 'PostgreSQL'],
                    'link': 'https://github.com/yourusername/portfolio'
                }
            ],
            'skills': [
                {
                    'category': 'Frontend',
                    'items': ['React', 'TypeScript', 'Tailwind CSS', 'HTML/CSS']
                },
                {
                    'category': 'Backend',
                    'items': ['Python', 'Django', 'Node.js', 'PostgreSQL']
                },
                {
                    'category': 'DevOps',
                    'items': ['Docker', 'Git', 'CI/CD', 'AWS']
                }
            ]
        })
        return resume

    @action(detail=False, methods=['get'])
    def download(self, request):
        resume = self.get_object()
        # Convert resume data to PDF using a template
        # This is a placeholder - you'll need to implement actual PDF generation
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="resume.pdf"'
        # Generate PDF here
        return response

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.request.user.is_staff:
            return ContactAdminSerializer
        return ContactSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAdmin]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Add IP and user agent
        serializer.validated_data['ip_address'] = request.META.get('REMOTE_ADDR')
        serializer.validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        contact = serializer.save()
        
        # Send email notification
        if hasattr(settings, 'ADMIN_EMAIL'):
            try:
                # Create HTML content for the email
                html_content = f'''
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .container {{ background-color: #f5f5f5; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e0e0e0; }}
                        .header {{ color: #2196f3; }}
                        .field {{ margin-bottom: 10px; }}
                        .field strong {{ display: inline-block; width: 80px; }}
                        .message {{ background-color: #e0e0e0; padding: 15px; border-radius: 4px; margin-top: 15px; }}
                        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666; }}
                    </style>
                </head>
                <body>
                    <h2 class="header">New Contact Form Submission</h2>
                    <div class="container">
                        <div class="field"><strong>Subject:</strong> {contact.subject}</div>
                        <div class="field"><strong>Name:</strong> {contact.name}</div>
                        <div class="field"><strong>Email:</strong> {contact.email}</div>
                        <div class="field"><strong>Message:</strong></div>
                        <div class="message">{contact.message}</div>
                    </div>
                    <div class="footer">
                        <p>This message was sent from the contact form on {settings.SITE_NAME}.</p>
                    </div>
                </body>
                </html>
                '''
                
                # Plain text version for email clients that don't support HTML
                plain_text = f'''
New Contact Form Submission

Subject: {contact.subject}
Name: {contact.name}
Email: {contact.email}

Message:
{contact.message}

This message was sent from the contact form on {settings.SITE_NAME}.
'''
                
                send_mail(
                    f'New Contact Form Submission: {contact.subject}',
                    plain_text,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    html_message=html_content,
                    fail_silently=False,
                )
                print(f"Email sent successfully to {settings.ADMIN_EMAIL}")
            except Exception as e:
                print(f"Error sending email: {str(e)}")
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
