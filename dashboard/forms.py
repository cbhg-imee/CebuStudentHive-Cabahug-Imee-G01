from django import forms

from accounts.forms import BootstrapFormMixin

from .models import Post


class PostForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "category", "location_tag", "body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 4})}
        help_texts = {"location_tag": "Example: a café name, or USC Talamban."}

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) < 10:
            raise forms.ValidationError("Description must be at least 10 characters long.")
        return body
