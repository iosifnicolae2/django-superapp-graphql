from django.contrib.auth import get_user_model
from django.http import JsonResponse
import os


class GraphQlTokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_key = os.getenv('GRAPHQL_API_KEY')

    def __call__(self, request):
        if request.path == '/graphql':
            auth_header = request.headers.get('Authorization')
            if not request.user.is_authenticated:
                if not self.api_key:
                    return JsonResponse({'error': 'Invalid Authorization token. GRAPHQL_API_KEY is missing.'}, status=401)
                if auth_header and auth_header.endswith(self.api_key):
                    # Authenticate user as first superuser
                    request.user = get_user_model().objects.filter(is_superuser=True).first()

        response = self.get_response(request)
        return response
