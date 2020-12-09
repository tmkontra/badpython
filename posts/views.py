from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views import View

import json

from .models import *

# Create your views here.
def index(request):
    post = _random_post()
    context = {
        "post": post
    }
    return render(request, "posts/index.html", context)

def _random_post():
    return Post.objects.raw(
        """
        SELECT * 
        FROM posts_post 
        LIMIT 1 
        OFFSET abs(random() % (select count(*) from posts_post ));
        """
    )[0]

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        try:
            ip = x_forwarded_for.split(',')[0].strip()
        except IndexError:
            ip= x_forwarded_for.strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class VoteView(View):
    def post(self, request, post_id, **kwargs):
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        is_bad = body.get("isBad")
        if is_bad is None or not isinstance(is_bad, bool):
            return HttpResponseBadRequest("isBad must be one of 'true' or 'false'")
        ip_addr = get_client_ip(request)
        if ip_addr is None:
            return HttpResponseForbidden("must provide ip address to vote")
        vote_field = VoteField.from_is_bad(is_bad)
        vote = Vote.new(ip_addr=ip_addr, post_id=post_id, is_bad=vote_field)
        if vote is None:
            return HttpResponse(status=202)
        else:
            vote.save()
            return JsonResponse({"vote": {"id": vote.id}})


        



