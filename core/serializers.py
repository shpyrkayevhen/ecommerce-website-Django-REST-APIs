# Аll available build in serializers: https://djoser.readthedocs.io/en/latest/settings.html
from djoser.serializers import UserSerializer as BaseUserSerializer, UserCreateSerializer as BaseUserCreateSerializer

from store.models import Customer


# Overwrite create users in auth/users endpoint
class UserCreateSerializer(BaseUserCreateSerializer):

    class Meta(BaseUserCreateSerializer.Meta):
        fields = ['id', 'username', 'password',
                  'email', 'first_name', 'last_name']
# Then registering DJOSER = {...} in the settings


# Overwrite getting current_user from auth/users/me endpoint
class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
# Then registering DJOSER = {...} in the settings
