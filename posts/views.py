import ast

from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views import View
from django.contrib import messages 


import json

from .exceptions import DuplicateError
from .models import *


# Create your views here.
class Index(View):
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
        try:
            return Post.objects.raw(
                f"""
                SELECT * 
                FROM posts_post
                {where}
                LIMIT 1 
                OFFSET abs(random() % (select count(*) - 1 from posts_post));
                """
            )[0]
        except:
            return None

index = Index.as_view()

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
        err, msg = parse_errors(code)
        if err:
            return JsonResponse({ "message": msg, "errors": err })
        ip_addr = get_client_ip(request)
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
    def get(self, request, post_id, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        post.code = post.code.strip()
        ip_addr = get_client_ip(request)
        if ip_addr is None:
            messages.warning(request, "Unable to submit a suggestion at this time.")
            return redirect("index")
        client = Client.get_or_create(ip_addr)
        if Suggestion.already_suggested(client.id, post_id):
            messages.warning(request, "You have already submitted a suggestion for that")
            return redirect("index")
        context = { "post": post }
        return render(request, "posts/suggest.html", context)
    
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
        ip_addr = get_client_ip(request)
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
        try:
            vote = Vote.new(ip_addr=ip_addr, post_id=post_id, is_bad=vote_field)
        except DuplicateError:
            return HttpResponse(status=202)
        else:
            vote.save()
            return JsonResponse({"vote": {"id": vote.id}})


        



