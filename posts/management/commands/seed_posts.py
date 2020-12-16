from ruamel.yaml import YAML
from django.core.management.base import BaseCommand, CommandError
from ...models import Post
from ...views import parse_errors


class Command(BaseCommand):
    help = 'Load a few initial posts'

    def _load_posts(self):
        yaml = YAML()
        fp = "posts/resources/posts.yaml"  
        with open(fp, "r") as f:
            posts = yaml.load(f)['posts']
        for title, code in posts.items():
            err, _ = parse_errors(code)
            if not err:
                yield Post(title=title, code=code)
            else: 
                raise Exception("Invalid code: %s", title)

    def handle(self, *args, **options):
        try:
            posts = list(self._load_posts())
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("Could not load posts: %s" % e))
            return
        for post in posts:
            post.save()
        self.stdout.write(
            self.style.SUCCESS('Successfully saved %s posts' % len(posts))
        )
