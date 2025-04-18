from django.shortcuts import render, get_object_or_404, redirect
from .models import Recipe, Comment
from .forms import RecipeForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import RecipeForm, CommentForm


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
