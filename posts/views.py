from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render

from .models import Post

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
