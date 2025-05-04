from django.db import models
from django.conf import settings
from users.models import CustomUser

class Recipe(models.Model):
    CATEGORY_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
    ]

    user  = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    ingredients = models.TextField(help_text="Enter ingredients separated by commas")
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    calorie_count = models.IntegerField(help_text="Calories in kcal")
    cooking_time = models.IntegerField(help_text="Time in minutes")
    allergic_content = models.CharField(max_length=255, blank=True, null=True)
    cooking_method = models.TextField(help_text="Enter steps separated by commas")
    category = models.CharField(
        max_length=10,
        choices=CATEGORY_CHOICES,
        default='veg',
        help_text="Select whether the recipe is Veg or Non-Veg"
    )

    # 🔥 If user is deleted, delete their recipes
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_ingredients_list(self):
        return [ingredient.strip() for ingredient in self.ingredients.split(",")] if self.ingredients else []

    def get_cooking_method_list(self):
        return [step.strip() for step in self.cooking_method.split(",")] if self.cooking_method else []


class Comment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)
    recipe = models.ForeignKey('Recipe',related_name='comments',on_delete=models.CASCADE)  
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username}"
    
# # Contact Form Model
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
