from rest_framework import serializers
from .models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'role', 'status', 'email_verified', 'password', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True}
        }

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class LoginResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = CustomUserSerializer()

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={'min_length': 'Mật khẩu phải có ít nhất 8 ký tự'}
    )

    password_confirm = serializers.CharField(write_only=True)
    
    full_name = serializers.CharField(max_length=255)
    role = serializers.ChoiceField(
        choices=['recruiter', 'company'],
        default='recruiter'
    )

    def validate(self, data):
        """Kiểm tra password và password_confirm khớp nhau"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Mật khẩu xác nhận không khớp'
            })
        return data


class RegisterResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = CustomUserSerializer()

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={'min_length': 'Mật khẩu phải có ít nhất 8 ký tự'}
    )
    
    new_password_confirm = serializers.CharField(write_only=True) # Xác thực lại mật khẩu
    
    def validate(self, data):
        """Kiểm tra new_password và new_password_confirm khớp nhau"""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Mật khẩu xác nhận không khớp'
            })
        return data

class VerifyEmailSerializer(serializers.Serializer):
    email_verification_token = serializers.CharField()

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Mật khẩu xác nhận không khớp'
            })
        return data

class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SocialAuthSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=['google', 'facebook', 'linkedin'])
    access_token = serializers.CharField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    role = serializers.CharField(default='recruiter')

class Verify2FASerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6, min_length=6)