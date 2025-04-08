from django.http import HttpResponse

def test_view(request):
    return HttpResponse("Django is working correctly!") 