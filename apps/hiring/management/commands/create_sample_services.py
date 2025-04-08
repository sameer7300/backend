from django.core.management.base import BaseCommand
from apps.hiring.models import ServiceType

class Command(BaseCommand):
    help = 'Creates sample service types for the hiring system'

    def handle(self, *args, **kwargs):
        services = [
            {
                'name': 'Web Development',
                'description': 'Custom web applications built with modern technologies like React, Django, and Node.js',
                'base_price': 2000,
                'order': 1,
            },
            {
                'name': 'Mobile App Development',
                'description': 'Native and cross-platform mobile apps for iOS and Android using React Native or Flutter',
                'base_price': 3000,
                'order': 2,
            },
            {
                'name': 'UI/UX Design',
                'description': 'Beautiful and intuitive user interfaces with a focus on user experience and accessibility',
                'base_price': 1500,
                'order': 3,
            },
            {
                'name': 'API Development',
                'description': 'RESTful and GraphQL APIs with proper documentation and security best practices',
                'base_price': 1800,
                'order': 4,
            },
            {
                'name': 'DevOps & Deployment',
                'description': 'Setup CI/CD pipelines, containerization, and cloud infrastructure on AWS/GCP/Azure',
                'base_price': 2500,
                'order': 5,
            },
        ]

        for service_data in services:
            ServiceType.objects.get_or_create(
                name=service_data['name'],
                defaults=service_data
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created service: {service_data["name"]}')
            )
