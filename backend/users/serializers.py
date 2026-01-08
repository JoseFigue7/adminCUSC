from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'can_manage_students', 'can_manage_payments',
                  'can_manage_academics', 'can_manage_scholarships', 'can_manage_thesis',
                  'can_view_reports', 'can_manage_users', 'can_manage_settings']


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone',
                  'role', 'role_id', 'is_active', 'password', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def create(self, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                user.role = role
            except Role.DoesNotExist:
                pass
        user.save()
        return user
    
    def update(self, instance, validated_data):
        role_id = validated_data.pop('role_id', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        if role_id is not None:
            try:
                role = Role.objects.get(id=role_id)
                instance.role = role
            except Role.DoesNotExist:
                instance.role = None
        
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        # Asignar rol de VIEWER por defecto
        try:
            viewer_role = Role.objects.get(name='VIEWER')
            user.role = viewer_role
            user.save()
        except Role.DoesNotExist:
            pass
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role', 'date_joined']



