from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views import View

import json

from .models import *

# Create your views here.
class Index(View):
    def get(self, request, **kwargs):
        previous_id = request.GET.get("p")
        post = _random_post(previous_id=previous_id)
        context = {
            "post": post
        }
        return render(request, "posts/index.html", context)

index = Index.as_view()

def _random_post(previous_id=None):
    post = None
    if previous_id:
        post_search = Post.objects.filter(pk=previous_id)
        if len(post_search) > 0:
            post = post_search[0]
    where = ""
    if post is not None:
        where = f"WHERE id != {post.id}"
    return Post.objects.raw(
        f"""
        SELECT * 
        FROM posts_post
        {where}
        LIMIT 1 
        OFFSET abs(random() % (select count(*) from posts_post {where}));
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


class SubmissionView(View):
    def get(self, request):
        context = { "submission": True }
        return render(request, "posts/submit.html", context)

    def post(self, request, **kwargs):
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        title, code = body.get("title"), body.get("code")
        if title is None or code is None:
            return HttpResponseBadRequest("must submit code and title!")
        ip_addr = get_client_ip(request)    
        post = Post.new(title, code, ip_addr)
        if post is None:
            return HttpResponseBadRequest("Unable to save your submission!")
        else:
            post.save()
            return redirect("index")


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


        



