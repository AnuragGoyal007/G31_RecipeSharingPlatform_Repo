from django.urls import path
from .views import home, recipe_detail, recipe_create, recipe_update, recipe_delete, my_recipes, edit_comment, delete_comment, contact_us

urlpatterns = [
    path('', home, name='home'),
    path('recipe/<int:pk>/', recipe_detail, name='recipe_detail'),
    path('recipe/new/', recipe_create, name='recipe_create'),
    path('recipe/<int:pk>/edit/', recipe_update, name='recipe_update'),
    path('recipe/<int:pk>/delete/', recipe_delete, name='recipe_delete'),
    path('my-recipes/', my_recipes, name='my_recipes'),
    path('comment/<int:pk>/edit/', edit_comment, name='edit_comment'),
    path('comment/<int:pk>/delete/', delete_comment, name='delete_comment'),
    path('contact-us/', contact_us, name='contact_us'),

]
