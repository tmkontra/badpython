from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("post/<int:post_id>/vote", views.VoteView.as_view(), name="vote"),
    path("post/submit", views.SubmissionView.as_view(), name="submit"),
    path("post/<int:post_id>/suggest", views.SuggestionView.as_view(), name="suggest"),
]
