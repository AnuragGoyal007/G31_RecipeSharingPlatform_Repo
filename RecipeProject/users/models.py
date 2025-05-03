from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='default-profile.jpg')
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    USER_TYPES = (
        ('user', 'Regular User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='user')

    REQUIRED_FIELDS = ['email']

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",
        blank=True
    )

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.is_superuser