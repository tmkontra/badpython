from collections import defaultdict
import datetime
import socket
from django.db import models
from django import utils

from .exceptions import DuplicateError


class PublishableMixin(models.Model):
    pub_date = models.DateTimeField("date published", auto_now_add=True)

    class Meta:
        abstract = True


class Post(PublishableMixin, models.Model):
    title = models.CharField(max_length=128, null=False)
    code = models.TextField(null=False)
    note = models.TextField(null=True)

    @classmethod
    def new(cls, title, code):
        return Post(title=title, code=code, note=None)

    def get_current_vote_counts(self):
        _id = self.id        
        vote_counts = (
            Vote
                .objects
                .filter(post__id=_id)
                .all()
                .values('post_id', 'is_bad')
                .annotate(count=models.Count('id'))
        )
        result = defaultdict(int)
        for count in vote_counts:
            if count['is_bad']:
                result['is_bad'] = count['count']
            else:
                result['not_bad'] = count['count']
        return result


class VoteField(models.BooleanField):
    description = "A Vote, good or bad code."

    @classmethod
    def from_is_bad(cls, is_bad: bool) -> bool:
        if is_bad is True:
            return VoteField.Bad()
        else:
            return VoteField.Good()

    @staticmethod
    def Good() -> bool:
        return False

    @staticmethod
    def Bad() -> bool:
        return True


class Vote(models.Model):
    post = models.ForeignKey(Post, null=False, on_delete=models.PROTECT)
    is_bad = VoteField(null=False, db_index=True)

    @classmethod
    def new(cls, post_id: int, is_bad: bool) -> "Vote":
        post = Post.objects.get(pk=post_id)
        if post is None:
            return None
        return Vote(post=post, is_bad=is_bad)


class Suggestion(PublishableMixin, models.Model):
    post = models.ForeignKey(Post, null=False, on_delete=models.PROTECT)
    code = models.TextField(null=False)
    description = models.TextField()

    @classmethod
    def new(cls, post_id: int, code: bytes, summary: str):
        post = Post.objects.get(pk=post_id)
        if post is None:
            return None
        return Suggestion(post=post, code=code, description=summary)
