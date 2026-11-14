from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.StudentDashboardView.as_view(), name="home"),
    path("admin/", views.AdminDashboardView.as_view(), name="admin_panel"),
    path("admin/moderate/<int:pk>/<str:action>/", views.ModeratePostView.as_view(), name="moderate"),
    path("submit/", views.SubmitPostView.as_view(), name="submit"),
    path("vote/<int:pk>/", views.VoteView.as_view(), name="vote"),
    path("comment/<int:pk>/", views.CommentView.as_view(), name="comment"),
]
