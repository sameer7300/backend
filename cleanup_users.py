import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count

User = get_user_model()

def cleanup_duplicate_users():
    # Find duplicate emails
    duplicates = User.objects.values('email').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    for dup in duplicates:
        email = dup['email']
        print(f"\nFound {dup['count']} users with email: {email}")
        
        # Get all users with this email
        users = User.objects.filter(email=email).order_by('date_joined')
        
        # Keep the oldest user (first created)
        keep_user = users.first()
        print(f"Keeping user: {keep_user.id} (created: {keep_user.date_joined})")
        
        # Delete the rest
        for user in users[1:]:
            print(f"Deleting user: {user.id} (created: {user.date_joined})")
            user.delete()

if __name__ == '__main__':
    cleanup_duplicate_users()
    print("\nDuplicate users cleanup completed!")
