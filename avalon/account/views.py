from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth.models import User

from .serializers import UserDetailSerializer, UserRegisterSerializer,  UserSerializerWithToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class UserDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer

    def perform_create(self, serializer):
        serializer.save()

#----------------------------------------------


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, user):
        token = super().validate(user)

        # Add custom claims
        # token['username'] = self.user.username
        # token['email'] = self.user.email

        # token['id'] = self.user.id
        # token['first_name'] = self.user.first_name
        # token['last_name'] = self.user.last_name
        # token['isAdmin'] = self.user.isAdmin

        # ...
        serializer = UserDetailSerializer(self.user).data

        for k, v in serializer.items():

            token[k]=v
        return token

    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# @api_view(['GET'])
# def getUsers(request):
#    users = User.object.all

#    serializer = UserDetailSerializer(users ,many=True)
#    return Response(serializer.data)