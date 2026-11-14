from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Post


class PostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "category", "location_tag", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"location_tag": "Example: a café name, or USC Talamban."}
