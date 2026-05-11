from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Role
from .serializers import (
    UserSerializer, RegisterSerializer, UserProfileSerializer, RoleSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .permissions import IsSuperAdmin, IsAdminOrSelf


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para login que retorna información del usuario"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            username = request.data.get('username')
            try:
                user = User.objects.get(username=username)
                user_data = UserProfileSerializer(user).data
                response.data['user'] = user_data
            except User.DoesNotExist:
                pass
        return response


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['create', 'destroy']:
            return [IsSuperAdmin()]
        elif self.action in ['update', 'partial_update']:
            return [IsAdminOrSelf()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Registro de nuevos usuarios"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """Obtener perfil del usuario actual"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Cambiar contraseña del usuario actual"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Se requieren old_password y new_password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Contraseña actual incorrecta'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Contraseña actualizada exitosamente'})
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def request_password_reset(self, request):
        """Solicitar recuperación de contraseña"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Generar token de recuperación
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # Construir URL de reset (frontend)
                frontend_url = settings.FRONTEND_URL
                reset_url = f"{frontend_url}/reset-password?token={token}&uid={uid}"
                
                # Enviar email
                subject = 'Recuperación de Contraseña - Colegio Santa Cecilia'
                message = f"""
Hola {user.get_full_name() or user.username},

Has solicitado recuperar tu contraseña. Para restablecer tu contraseña, haz clic en el siguiente enlace:

{reset_url}

Este enlace expirará en 24 horas.

Si no solicitaste este cambio, puedes ignorar este correo.

Saludos,
Colegio Santa Cecilia
                """
                
                try:
                    send_mail(
                        subject,
                        message,
                        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@admincusc.local'),
                        [email],
                        fail_silently=False,
                    )
                except Exception as e:
                    # Log error pero no revelar si el email existe
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Error al enviar email de recuperación: {str(e)}')
                
                # Siempre retornar éxito por seguridad (no revelar si el email existe)
                return Response({
                    'message': 'Si el email existe, recibirás un correo con las instrucciones para recuperar tu contraseña.'
                }, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Por seguridad, no revelamos si el email existe o no
                return Response({
                    'message': 'Si el email existe, recibirás un correo con las instrucciones para recuperar tu contraseña.'
                }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def confirm_password_reset(self, request):
        """Confirmar y cambiar contraseña con token"""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            # Extraer uid del token si está en el formato uid-token
            # O recibirlo directamente del request
            uid = request.data.get('uid')
            
            if not uid:
                return Response(
                    {'error': 'UID es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                # Decodificar uid
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                
                # Verificar token
                if not default_token_generator.check_token(user, token):
                    return Response(
                        {'error': 'Token inválido o expirado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Cambiar contraseña
                user.set_password(new_password)
                user.save()
                
                return Response({
                    'message': 'Contraseña restablecida exitosamente'
                }, status=status.HTTP_200_OK)
                
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {'error': 'Token inválido o expirado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para roles (solo lectura)"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]




