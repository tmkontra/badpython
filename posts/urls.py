from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("post/<int:post_id>/vote", views.VoteView.as_view(), name="vote"),
    path("post/submit", views.SubmissionView.as_view(), name="submit"),
    path("post/<int:post_id>/suggest", views.SuggestionView.as_view(), name="suggest"),
    path("post/<int:post_id>/suggestions",
         views.PostSuggestionView.as_view(), name="suggestions"),
    path("post/<int:post_id>/suggestions/<int:suggestion_id>",
         views.PostSuggestionDetailView.as_view(), name="suggestion_detail"),
]
