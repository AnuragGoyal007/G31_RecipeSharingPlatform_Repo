from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Comment, ContactMessage
from .forms import RecipeForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import RecipeForm, CommentForm, ContactForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as django_login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm

#--------------------------------------------------------------------------------------------------------------

from .api_client import FlaskAPIClient, FlaskAPIError


def recipe_list(request):
    client = FlaskAPIClient()
    
    try:
        recipes = client.get_recipes()
        if not recipes:  # Handle empty response
            messages.warning(request, 'No recipes found')
            recipes = []
        return render(request, 'recipes/list.html', {'recipes': recipes})
    except FlaskAPIError as e:
        messages.error(request, f'API Error: {str(e)}')
        return render(request, 'recipes/list.html', {'recipes': []})
    except Exception as e:
        messages.error(request, f'Unexpected error: {str(e)}')
        return render(request, 'recipes/list.html', {'recipes': []})
    

def flask_recipe_detail(request, pk):
    client = FlaskAPIClient()
    try:
        recipe = client.get_recipe(pk)  # Assuming get_recipe is a method in FlaskAPIClient
        return render(request, 'recipes/flask_recipe_detail.html', {'recipe': recipe})
    except Exception as e:
        return render(request, 'error.html', {'message': str(e)})
    
    
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Both username and password are required')
            return render(request, 'users/login.html')
        
        # Authenticate via Flask API
        client = FlaskAPIClient()
        try:
            auth_result = client.login(username, password)
            
            if auth_result and auth_result.get('access_token'):
                # Get or create Django user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': auth_result.get('user', {}).get('email', ''),
                        'is_active': True
                    }
                )
                
                if created:
                    user.set_unusable_password()
                    user.save()
                
                # Store Flask token in session
                request.session['flask_token'] = auth_result['access_token']
                
                # Login user in Django
                django_login(request, user)
                messages.success(request, 'Logged in successfully!')
                return redirect('home')
            
            messages.error(request, 'Invalid credentials')
        except Exception as e:
            messages.error(request, f'Login failed: {str(e)}')
    
    return render(request, 'users/login.html')

@login_required
def user_logout(request):
    # Clear the Flask API token from session
    if 'flask_token' in request.session:
        del request.session['flask_token']
    
    # Perform Django logout
    django_logout(request)
    
    # Add success message and redirect
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')  # or your preferred redirect target

@login_required
def flask_recipe_create(request):
    if not request.session.get('flask_token'):
        messages.error(request, "Please login to create recipes")
        return redirect('user_login')

    if request.method == 'POST':
        try:
            form_data = {
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'ingredients': request.POST.get('ingredients'),
                'cooking_method': request.POST.get('cooking_method'),
                'calorie_count': int(request.POST.get('calorie_count')),
                'cooking_time': int(request.POST.get('cooking_time')),
                'category': request.POST.get('category'),
                'user_id': request.user.id
            }
            
            client = FlaskAPIClient(request)
            response = client.create_recipe(form_data)
            messages.success(request, "Recipe created successfully!")
            return redirect('flask_recipe_detail', pk=response.get('id'))
            
        except ValueError as e:
            messages.error(request, f"Invalid data: {str(e)}")
        except FlaskAPIError as e:
            messages.error(request, f"API Error: {str(e)}")
        except Exception as e:
            messages.error(request, f"Unexpected error: {str(e)}")
        
        # Preserve form data on error
        return render(request, 'recipes/flask_recipe_create.html', {
            'form_data': request.POST.dict(),
            'error': str(e) if 'e' in locals() else None
        })
    
    return render(request, 'recipes/flask_recipe_create.html')




#----------------------------------------------------------------------------------

def home(request):
    category = request.GET.get('category')
    if category == 'veg':
        recipes = Recipe.objects.filter(category='veg')
    elif category == 'nonveg':
        recipes = Recipe.objects.filter(category='nonveg')
    else:
        recipes = Recipe.objects.all()
    return render(request, 'recipes/home.html', {'recipes': recipes})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    comments = recipe.comments.all()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in to comment.")

        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.recipe = recipe
            comment.user = request.user
            comment.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = CommentForm()

    return render(request, 'recipes/recipe_detail.html', {
        'recipe': recipe,
        'comments': comments,
        'comment_form': form,
    })


@login_required
def recipe_create(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()
            return redirect('recipe_detail', pk=recipe.pk)
        else:
            # In your recipe_create view, add:
            print(form.errors) if form.is_valid() else None  # Debugging line
    else:
        form = RecipeForm()
    return render(request, 'recipes/recipe_create.html', {'form': form})

@login_required
def my_recipes(request):
    recipes = Recipe.objects.filter(created_by=request.user)
    return render(request, 'recipes/my_recipes.html', {'recipes': recipes})


@login_required
def recipe_update(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)


    if recipe.created_by != request.user and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("You are not allowed to edit this recipe.")

    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        if form.is_valid():
            form.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)

    return render(request, 'recipes/recipe_update.html', {
        'form': form,
        'recipe': recipe
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from .models import Recipe

@login_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)

    
    if recipe.created_by != request.user and not request.user.is_staff and not request.user.is_superuser:
        return HttpResponseForbidden("You are not allowed to delete this recipe.")

    if request.method == 'POST':
        recipe.delete()
        return redirect('my_recipes')  

    return render(request, 'recipes/recipe_delete.html', {'recipe': recipe})


@login_required
def edit_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this comment.")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('recipe_detail', pk=comment.recipe.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'recipes/edit_comment.html', {'form': form})

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if comment.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    if request.method == 'POST':
        comment.delete()
        return redirect('recipe_detail', pk=comment.recipe.pk)
    return render(request, 'recipes/delete_comment.html', {'comment': comment})

# # Contact Form View
def contact_us(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message']
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('home')
    else:
        form = ContactForm()
    
    return render(request, 'recipes/contact_us.html', {'form': form})