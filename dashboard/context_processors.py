from .forms import PostForm


def submit_form(request):
    if request.user.is_authenticated:
        return {"submit_form": PostForm(auto_id="submit_%s")}
    return {}
