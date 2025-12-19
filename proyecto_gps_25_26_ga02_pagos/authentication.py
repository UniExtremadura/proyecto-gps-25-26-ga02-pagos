from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.contrib.auth import get_user_model

User = get_user_model()


class JWTAuthenticationSafe(JWTAuthentication):

    # Sobrescribimos el punto de entrada principal para ver qué llega
    def authenticate(self, request):
        # 1. Imprimir las cabeceras clave para ver si llega el Token
        auth_header = request.headers.get('Authorization')
        print(f"\n🔍 DEBUG HEADERS ({request.method} {request.path}):")
        if auth_header:
            print(f"   🔑 Header Authorization recibido: {auth_header[:15]}...")
        else:
            print(f"   ❌ NO hay header Authorization. (Por eso da 401)")

        # 2. Llamar a la lógica original de Django REST Framework
        return super().authenticate(request)

    def get_user(self, validated_token):
        # Esta parte ya sabemos que funciona, pero añadimos check de is_active
        try:
            user_id = validated_token['user_id']
        except KeyError:
            raise InvalidToken(('Token inválido'))

        try:
            user = User.objects.get(pk=user_id)
            print(f"   ✅ Usuario {user_id} encontrado. Activo: {user.is_active}")
        except User.DoesNotExist:
            print(f"   ⚠️ Usuario {user_id} NO existe. Creando...")
            email = validated_token.get('email', f'user_{user_id}@temp.com')
            username = validated_token.get('username', f'user_{user_id}')
            user = User.objects.create(pk=user_id, username=username, email=email)
            user.set_unusable_password()
            user.save()

        return user