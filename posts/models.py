from django.db import models


class PublishableMixin(models.Model):
    pub_date = models.DateTimeField('date published')

    class Meta:
        abstract = True


class Post(PublishableMixin, models.Model):
    title = models.CharField(max_length=128, null=False)
    code = models.TextField(null=False)
    note = models.TextField()


class Suggestion(PublishableMixin, models.Model):
    code = models.TextField()
    description = models.TextField()