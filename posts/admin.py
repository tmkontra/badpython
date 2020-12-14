from django import forms
from django.contrib import admin
from .models import Post, Vote, Suggestion


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    pass

@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    pass
