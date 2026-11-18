from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView

from accounts.models import User
from accounts.views import role_home

from .forms import PostForm
from .models import Comment, Post, Vote


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Anonymous -> login page. Wrong role -> 403.html."""
    required_role = None

    def test_func(self):
        return self.request.user.role == self.required_role


class StudentRequiredMixin(RoleRequiredMixin):
    required_role = User.Role.STUDENT


class AdminRequiredMixin(RoleRequiredMixin):
    required_role = User.Role.ADMIN


class StudentDashboardView(StudentRequiredMixin, ListView):
    template_name = "dashboard/home.html"
    context_object_name = "posts"
    paginate_by = 15

    def get_queryset(self):
        score = Vote.objects.filter(post=OuterRef("pk")).values("post").annotate(s=Sum("value")).values("s")
        qs = (Post.objects.filter(status=Post.Status.APPROVED).select_related("author")
              .annotate(score=Coalesce(Subquery(score), 0), comment_count=Count("comments", distinct=True)))
        g = self.request.GET
        if g.get("cat") in Post.Category.values:
            qs = qs.filter(category=g["cat"])
        if q := g.get("q", "").strip():
            qs = qs.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(location_tag__icontains=q))
        sort = g.get("sort")
        if sort == "top":
            return qs.filter(score__gte=3).order_by("-score", "-created_at")
        if sort == "recent":
            return qs.order_by("-created_at")
        return qs.order_by("-score", "-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        posts = list(ctx["posts"])
        votes = dict(Vote.objects.filter(user=self.request.user, post__in=posts).values_list("post_id", "value"))
        nodes = {}
        comments = Comment.objects.filter(post__in=posts).select_related("author").order_by("created_at")
        for c in comments:
            c.child_list = []
            nodes[c.pk] = c
        roots = {p.pk: [] for p in posts}
        for c in nodes.values():
            if c.parent_id in nodes:
                nodes[c.parent_id].child_list.append(c)
            else:
                roots[c.post_id].append(c)
        for p in posts:
            p.user_vote = votes.get(p.pk, 0)
            p.root_comments = roots[p.pk]
        ctx["posts"] = posts
        ctx["active_cat"] = self.request.GET.get("cat", "")
        ctx["active_sort"] = self.request.GET.get("sort", "")
        ctx["q"] = self.request.GET.get("q", "")
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs"] = ("&" + params.urlencode()) if params else ""
        return ctx


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "dashboard/admin_panel.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        pending = Post.objects.filter(status=Post.Status.PENDING).select_related("author").order_by("created_at")
        if q:
            pending = pending.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(location_tag__icontains=q) | Q(author__email__icontains=q))
        counts = dict(Post.objects.values_list("status").annotate(n=Count("id")))
        ctx.update(
            q=q, pending=pending,
            kpis=[
                ("Pending review", counts.get("PENDING", 0), "hourglass-split", "warning"),
                ("Approved posts", counts.get("APPROVED", 0), "check-circle", "success"),
                ("Rejected posts", counts.get("REJECTED", 0), "x-circle", "danger"),
                ("Students", User.objects.filter(role=User.Role.STUDENT).count(), "people", "primary"),
                ("Votes cast", Vote.objects.count(), "hand-thumbs-up", "info"),
                ("Comments", Comment.objects.count(), "chat-left-text", "secondary"),
            ],
            recent=Post.objects.exclude(status=Post.Status.PENDING).select_related("author").order_by("-reviewed_at")[:8],
        )
        return ctx


class ModeratePostView(AdminRequiredMixin, View):
    def post(self, request, pk, action):
        if action not in ("approve", "reject"):
            raise Http404
        post = get_object_or_404(Post, pk=pk)
        post.status = Post.Status.APPROVED if action == "approve" else Post.Status.REJECTED
        post.reviewed_at = timezone.now()
        post.save(update_fields=["status", "reviewed_at"])
        messages.success(request, f"“{post.title}” {post.get_status_display().lower()}.")
        return redirect("dashboard:admin_panel")


class SubmitPostView(StudentRequiredMixin, View):
    def post(self, request):
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            messages.success(request, "Submitted. An admin will review it before it appears in the feed.")
            post.save()
        else:
            errs = "; ".join(f"{f}: {e[0]}" for f, e in form.errors.items())
            messages.error(request, f"Could not submit. {errs}")
        return redirect(role_home(request.user))


class VoteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, status=Post.Status.APPROVED)
        try:
            value = int(request.POST.get("value", ""))
        except ValueError:
            return JsonResponse({"error": "bad value"}, status=400)
        if value not in (1, -1):
            return JsonResponse({"error": "bad value"}, status=400)
        vote = Vote.objects.filter(user=request.user, post=post).first()
        if vote and vote.value == value:
            vote.delete()
            current = 0
        else:
            Vote.objects.update_or_create(user=request.user, post=post, defaults={"value": value})
            current = value
        score = post.votes.aggregate(s=Coalesce(Sum("value"), 0))["s"]
        return JsonResponse({"score": score, "user_vote": current})


class CommentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk, status=Post.Status.APPROVED)
        body = request.POST.get("body", "").strip()[:1000]
        parent = None
        if request.POST.get("parent"):
            parent = get_object_or_404(Comment, pk=request.POST["parent"], post=post)
        if body:
            Comment.objects.create(post=post, author=request.user, parent=parent, body=body)
        else:
            messages.error(request, "Write something before posting a comment.")
        return redirect(f"{reverse('dashboard:home')}#post-{post.pk}")


class MySubmissionsView(StudentRequiredMixin, ListView):
    template_name = "dashboard/my_submissions.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


class SubmissionUpdateView(StudentRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "dashboard/submission_form.html"
    success_url = reverse_lazy("dashboard:my_submissions")

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user, status=Post.Status.PENDING)

    def form_valid(self, form):
        messages.success(self.request, "Submission updated. It remains pending admin review.")
        return super().form_valid(form)


class SubmissionDeleteView(StudentRequiredMixin, DeleteView):
    model = Post
    template_name = "dashboard/submission_confirm_delete.html"
    success_url = reverse_lazy("dashboard:my_submissions")

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user, status=Post.Status.PENDING)

    def form_valid(self, form):
        messages.success(self.request, "Pending submission deleted.")
        return super().form_valid(form)
