import datetime
import socket
from django.db import models
from django import utils


class PublishableMixin(models.Model):
    pub_date = models.DateTimeField(
        'date published', 
        default=utils.timezone.now
    )

    class Meta:
        abstract = True


class Client(models.Model):
    ip_address = models.BinaryField(max_length=16, null=False, db_index=True, unique=True)

    @classmethod
    def from_ip(cls, ip_addr: str) -> 'Client':
        b = cls.aton(ip_addr)
        return Client(ip_address=b)

    @staticmethod
    def aton(addr: str):
        return socket.inet_aton(addr)
    
    @staticmethod
    def ntoa(packed_ip: bytes):
        return socket.inet_ntoa(packed_ip)

    @classmethod 
    def get_or_create(cls, ip_addr: str):
        client, created = Client.objects.get_or_create(ip_address=cls.aton(ip_addr))
        return client


class Post(PublishableMixin, models.Model):
    title = models.CharField(max_length=128, null=False)
    code = models.TextField(null=False)
    client = models.ForeignKey(Client, null=True, on_delete=models.PROTECT)
    note = models.TextField(null=True)

    @classmethod
    def new(cls, title, code, client_ip=None):
        if client_ip is not None:
            client = Client.get_or_create(client_ip)
        else:
            client = None
        return Post(title=title, code=code, client=client, note=None)


class VoteField(models.BooleanField):
    description = "A Vote, good or bad."

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
    client = models.ForeignKey(Client, null=False, on_delete=models.PROTECT)
    post = models.ForeignKey(Post, null=False, on_delete=models.PROTECT)
    is_bad = VoteField(null=False, db_index=True)

    @classmethod
    def already_voted(cls, client_id, post_id):
        existing = Vote.objects.filter(client__id=client_id, post__id=post_id)
        return len(existing) > 0

    @classmethod
    def new(cls, ip_addr: str, post_id: int, is_bad: bool) -> 'Vote':
        client = Client.get_or_create(ip_addr)
        post = Post.objects.get(pk=post_id)
        if post is None:
            return None
        if cls.already_voted(client.id, post_id):
            return None
        return Vote(client=client, post=post, is_bad=is_bad)


class Suggestion(PublishableMixin, models.Model):
    code = models.TextField()
    description = models.TextField()
