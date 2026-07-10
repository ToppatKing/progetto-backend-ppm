from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer di lettura/aggiornamento per il profilo dell'utente stesso."""

    role = serializers.ReadOnlyField()

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "bio",
            "role",
            "date_joined",
        ]
        read_only_fields = ["id", "username", "role", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Crea un nuovo account cliente. La registrazione non concede mai l'accesso staff."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        ]

    def validate_email(self, value):
        if value and CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        # La registrazione crea sempre un ruolo "customer" standard. Gli
        # account admin vengono creati separatamente (vedi i dati demo /
        # createsuperuser).
        user.is_staff = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Valida le credenziali username/password e restituisce l'utente autenticato."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get("username"), password=attrs.get("password")
        )
        if not user:
            raise serializers.ValidationError(
                "Unable to log in with the provided credentials.", code="authorization"
            )
        if not user.is_active:
            raise serializers.ValidationError("This account has been disabled.")
        attrs["user"] = user
        return attrs
