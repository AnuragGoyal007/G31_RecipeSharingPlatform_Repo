from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, blank=False, null=False)  # 👈 Add this
    
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='default-profile.jpg')
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    USER_TYPES = (
        ('admin', 'Admin'),
        ('user', 'User'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='user')

    REQUIRED_FIELDS = ['email']  # You can also include 'first_name', 'last_name' if needed

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

    def save(self, *args, **kwargs):
        if self.user_type == 'admin':
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.user_type == 'admin'

    def is_normal_user(self):
        return self.user_type == 'user'