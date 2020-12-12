import ast
from functools import partial
import json

from django.contrib import messages
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse, HttpResponseNotFound
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from ratelimit.decorators import ratelimit

from .exceptions import DuplicateError
from .models import *
from django.core.cache.backends import locmem


def ratelimited(request, *args, **kwargs):
    return HttpResponse(status=429, content="Too many requests, please slow down!")


GLOBAL_REQUEST_GROUP = "global"
limit = ratelimit(key="header:client-ip", method="GET",
                  rate="5/s", block=True, group=GLOBAL_REQUEST_GROUP)

class Index(View):
    @method_decorator(limit)
    def get(self, request, **kwargs):
        previous_id = request.GET.get("p")
        post = self._random_post(previous_id=previous_id)
        if post is None:
            messages.error(request, "No more posts to view, submit your own!")
            return redirect("submit")
        context = {
            "post": post
        }
        return render(request, "posts/index.html", context)

    @classmethod
    def _random_post(cls, previous_id=None):
        post = None
        if previous_id:
            post_search = Post.objects.filter(pk=previous_id)
            if len(post_search) > 0:
                post = post_search[0]
        where = ""
        if post is not None:
            where = f"WHERE id != {post.id}"
        print("where", where)
        try:
            sql = f"""
                SELECT * 
                FROM posts_post
                {where}
                LIMIT 1 
                OFFSET floor(random() * (select count(*) from posts_post {where}));
                """
            print(sql)
            return Post.objects.raw(sql)[0]
        except Exception as e:
            print("could not get random", e)
            return None

index = Index.as_view()


class SubmissionView(View):
    @method_decorator(limit)
    def get(self, request):
        context = { "submission": True }
        return render(request, "posts/submit.html", context)


    @method_decorator(limit)
    def post(self, request, **kwargs):
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        title, code = body.get("title"), body.get("code")
        if title is None or code is None:
            return HttpResponseBadRequest("must submit code and title!")
        err, msg = parse_errors(code)
        if err:
            return JsonResponse({ "message": msg, "errors": err })
        ip_addr = request.META.get("CLIENT_IP")
        if ip_addr is None:
            messages.warning(request, "Unable to submit at this time.")
            return redirect("index")
        post = Post.new(title, code, ip_addr)
        if post is None:
            return HttpResponseBadRequest("Unable to save your submission!")
        else:
            post.save()
            messages.success(request, "Submitted successfully!")
            return redirect("index")

def parse_errors(code):
    if not (code and code.strip()):
        return True, "Submission must not be empty"
    try:
        ast.parse(code)
    except SyntaxError as e:
        return [
            {
                "lineNum": e.lineno,
                "reason": e.msg,
            },
        ], "Code must be valid python. Please try again."
    return None, None

class SuggestionView(View):
    @method_decorator(limit)
    def get(self, request, post_id, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        post.code = post.code.strip()
        ip_addr = request.META.get("CLIENT_IP")
        if ip_addr is None:
            messages.warning(request, "Unable to submit a suggestion at this time.")
            return redirect("index")
        client = Client.get_or_create(ip_addr)
        if Suggestion.already_suggested(client.id, post_id):
            messages.warning(request, "You have already submitted a suggestion for that")
            return redirect("index")
        context = { "post": post }
        return render(request, "posts/suggest.html", context)
    
    @method_decorator(limit)
    def post(self, request, post_id, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        code, summary = body.get("code"), body.get("summary")
        if code is None or summary is None:
            return HttpResponseBadRequest("must include code and summary")
        err, msg = parse_errors(code)
        if err:
            return JsonResponse({"message": msg, "errors": err})
        ip_addr = request.META.get("CLIENT_IP")
        if ip_addr is None:
            return HttpResponseForbidden("must provide ip address to vote")
        try:
            suggestion = Suggestion.new(post.id, code, summary, ip_addr)
        except DuplicateError as e:
            messages.warning("You have already submitted a suggestion for that.")
            return redirect("index")
        else:
            suggestion.save()
            return redirect("index")


class VoteView(View):
    @method_decorator(limit)
    def post(self, request, post_id, **kwargs):
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        is_bad = body.get("isBad")
        if is_bad is None or not isinstance(is_bad, bool):
            return HttpResponseBadRequest("isBad must be one of 'true' or 'false'")
        ip_addr = request.META.get("CLIENT_IP")
        if ip_addr is None:
            return HttpResponseForbidden("must provide ip address to vote")
        vote_field = VoteField.from_is_bad(is_bad)
        try:
            vote = Vote.new(ip_addr=ip_addr, post_id=post_id, is_bad=vote_field)
        except DuplicateError:
            return HttpResponse(status=202)
        else:
            vote.save()
            return JsonResponse({"vote": {"id": vote.id}})


        



