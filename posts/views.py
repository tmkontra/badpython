import ast
from functools import partial
import json
import logging

from django.contrib import messages
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
    HttpResponseNotFound,
)
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from ratelimit.decorators import ratelimit

from .exceptions import DuplicateError
from .models import *
from django.core.cache.backends import locmem


logger = logging.getLogger("posts.views")


def ratelimited(request, *args, **kwargs):
    logger.info("Rate limit reached for request", request.META["CLIENT_IP"])
    return HttpResponse(status=429, content="Too many requests, please slow down!")


GLOBAL_REQUEST_GROUP = "global"

limit = ratelimit(
    key="header:client-ip",
    method="GET",
    rate="5/s",
    block=True,
    group=GLOBAL_REQUEST_GROUP,
)


class Index(View):
    @method_decorator(limit)
    def get(self, request, **kwargs):
        previous_id = request.GET.get("p")
        post = self._random_post(previous_id=previous_id)
        if post is None:
            logger.debug("Exhausted all posts")
            messages.error(request, "No more posts to view, submit your own!")
            return redirect("submit")
        context = {"post": post}
        context.update(self._session_context(request, post))
        self._update_seen(request, post)
        return render(request, "posts/index.html", context)

    def _session_context(self, request, post):
        s = request.session
        logger.debug("Session: %s", s.items())
        sugg = s.get("suggestions", dict())
        suggestion_id = sugg.get(str(post.id))
        vote = s.get("votes", dict()).get(str(post.id))
        subs = s.get("submission", list())
        print(suggestion_id, vote, subs)
        context = {}
        if suggestion_id:
            context.update({"suggestion": suggestion_id})
        if vote is not None:
            context.update({"vote": vote})
        if str(post.id) in subs:
            context.update({"posted_by_user": True})
        logger.debug("session context: %s", context)
        return context

    def _update_seen(self, request, post):
        seen = request.session.setdefault("posts_seen", list())
        if post.id not in seen:
            seen.append(post.id)
        request.session["posts_seen"] = seen
        request.session.modified = True

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
            logger.debug("filtering previous post: %s", where)
        try:
            sql = f"""
                SELECT * 
                FROM posts_post
                {where}
                LIMIT 1 
                OFFSET floor(random() * (select count(*) from posts_post {where}));
                """
            return Post.objects.raw(sql)[0]
        except Exception as e:
            logger.exception("could not get random post")
            return None


index = Index.as_view()


class SubmissionView(View):
    @method_decorator(limit)
    def get(self, request):
        context = {"submission": True}
        return render(request, "posts/submit.html", context)

    @method_decorator(limit)
    def post(self, request, **kwargs):
        try:
            body = json.loads(request.body)
        except Exception as e:
            logger.exception("Got invalid submission body")
            return HttpResponseBadRequest("could not parse body!")
        title, code = body.get("title"), body.get("code")
        if title is None or code is None:
            logger.error("Submission missing title [%s] or code [%s]", title, code)
            return HttpResponseBadRequest("must submit code and title!")
        err, msg = parse_errors(code)
        if err:
            return JsonResponse({"message": msg, "errors": err})
        post = Post.new(title, code)
        if post is None:
            return HttpResponseBadRequest("Unable to save your submission!")
        else:
            post.save()
            self._update_session(request, post)
            messages.success(request, "Submitted successfully!")
            return redirect("index")

    def _update_session(self, request, post):
        posts = request.session.setdefault("posts", list())
        posts.append(post.id)
        request.session["posts"] = posts
        request.session.modified = True
        logger.debug("Session: %s", request.session)


def parse_errors(code):
    if not (code and code.strip()):
        return True, "Submission must not be empty"
    try:
        ast.parse(code)
    except SyntaxError as e:
        logger.exception("Could not parse invalid python: %s", code)
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
        existing = request.session.setdefault("suggestions", dict())
        logger.debug("Existing suggestions %s", existing)
        if str(post_id) in existing:
            logger.info("Session cannot submit another suggestion")
            messages.warning(
                request, "You have already submitted a suggestion for that"
            )
            return redirect("index")
        context = {"post": post}
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
        suggestion = Suggestion.new(post.id, code, summary)
        suggestion.save()
        self._update_session(request, post, suggestion)
        return redirect("index")

    def _update_session(self, request, post, suggestion):
        suggestions = request.session.setdefault("suggestions", dict())
        if post.id not in suggestions:
            suggestions[post.id] = suggestion.id
        request.session["suggestions"] = suggestions
        request.session.modified = True
        logger.debug("Session: %s", request.session)


class VoteView(View):
    @method_decorator(limit)
    def post(self, request, post_id, **kwargs):
        post = get_object_or_404(Post, pk=post_id)
        try:
            body = json.loads(request.body)
        except:
            return HttpResponseBadRequest("could not parse body!")
        is_bad = body.get("isBad")
        if is_bad is None or not isinstance(is_bad, bool):
            return HttpResponseBadRequest("isBad must be one of 'true' or 'false'")
        vote_field = VoteField.from_is_bad(is_bad)
        vote = Vote.new(post_id=post.id, is_bad=vote_field)
        if vote is None:
            return HttpResponse(status=500)
        else:
            vote.save()
            self._update_session(request, post, vote)
            return JsonResponse(
                {
                    "vote": {
                        "id": vote.id,
                    }
                }
            )

    def _update_session(self, request, post, vote):
        votes = request.session.setdefault("votes", dict())
        if post.id not in votes:
            votes[post.id] = vote.is_bad
        request.session["votes"] = votes
        request.session.modified = True
        logger.debug("Session: %s", request.session)
