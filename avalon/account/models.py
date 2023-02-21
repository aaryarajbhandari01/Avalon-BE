from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from avalon.abstract_models import TimestampAbstractModel


class User(AbstractUser):
    def __str__(self):
        return self.username
