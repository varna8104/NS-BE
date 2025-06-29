from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Complaint, CustomUser

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password', 'confirm_password', 'first_name', 'last_name', 'user_type', 'cop_id')
        extra_kwargs = {
            'user_type': {'read_only': True},
            'cop_id': {'read_only': True}
        }
    
    def validate(self, data):
        if 'confirm_password' in data and data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        confirm_password = validated_data.pop('confirm_password', None)
        user_type = validated_data.get('user_type', 'user')
        
        if user_type == 'cop':
            validated_data['user_type'] = 'cop'
            validated_data['cop_id'] = validated_data['username']
        
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'user'),
            cop_id=validated_data.get('cop_id', None)
        )
        return user

class CopSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('id', 'cop_id', 'password', 'confirm_password', 'first_name', 'last_name', 'email')
    
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        confirm_password = validated_data.pop('confirm_password')
        cop_id = validated_data['cop_id']
        
        user = CustomUser.objects.create_user(
            username=cop_id,
            cop_id=cop_id,
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type='cop'
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    user_type = serializers.CharField(required=False)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type', 'user')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.user_type != user_type:
                    raise serializers.ValidationError(f'Invalid login for {user_type} zone')
                data['user'] = user
                return data
            else:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError('Must include username and password')

class ComplaintSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    submitted_at = serializers.DateTimeField(format='%Y-%m-%d', read_only=True)
    
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ['emotion', 'priority', 'user', 'submitted_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ComplaintStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['status', 'review_notes']