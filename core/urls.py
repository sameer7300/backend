"""
URL configuration for portfolio project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.payments.views import create_payment_intent, webhook
from .views import test_view
from apps.portfolio.test_email import test_email

api_v1_patterns = [
    path('accounts/', include('apps.accounts.urls')),
    path('portfolio/', include('apps.portfolio.urls')),
    path('hiring/', include('apps.hiring.urls')),
    path('payments/', include('apps.payments.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('user-dashboard/', include('apps.user_dashboard.urls')),
    path('chat/', include('apps.portfolio_chat.urls')),  # Add chat URLs
    path('create-payment-intent/', create_payment_intent, name='create-payment-intent'),
    path('webhook/', webhook, name='webhook'),
]

urlpatterns = [
    path('', test_view, name='test'),  # Add test view at root URL
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1_patterns)),
    path('test-email/', test_email, name='test_email'),  # Add test email view
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
