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

# ✅ ContactForm
class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': 'Your Name',
        'class': 'form-control'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Your Email',
        'class': 'form-control'
    }))
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'placeholder': 'Subject',
        'class': 'form-control'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Your Message',
        'class': 'form-control',
        'rows': 5
    }))

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField()