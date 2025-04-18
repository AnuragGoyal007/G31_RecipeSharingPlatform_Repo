from django import forms
from .models import Recipe, Comment

# ✅ Single RecipeForm
class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = [
            'title',
            'description',
            'image',
            'calorie_count',
            'cooking_time',
            'allergic_content',
            'ingredients',
            'cooking_method',
            'category',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'ingredients': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter each ingredient separated by commas'}),
            'cooking_method': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter each step separated by commas'}),
            'category': forms.Select(choices=Recipe.CATEGORY_CHOICES),
            'allergic_content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter allergic content information'}),  # Add textarea widget for allergic content
        }
        labels = {
            'cooking_method': 'Instructions'
            ,'allergic_content': 'Allergic Content',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['calorie_count'].required = True
        self.fields['cooking_time'].required = True

# ✅ Add CommentForm
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']  # ✅ Correct field name from your model
