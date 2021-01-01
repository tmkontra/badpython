from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from ...models import Post, PostApproval
from ...views import parse_errors


# Approvals
# 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19
# Deletes
# 15, 16, 17, 20

class Command(BaseCommand):
    help = 'Approve posts'

    # def _load_posts(self):
    #     yaml = YAML()
    #     fp = "posts/resources/posts.yaml"
    #     with open(fp, "r") as f:
    #         posts = yaml.load(f)['posts']
    #     for title, code in posts.items():
    #         err, _ = parse_errors(code)
    #         if not err:
    #             yield Post(title=title, code=code)
    #         else:
    #             raise Exception("Invalid code: %s", title)

    approvals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18, 19]
    deletes = [15, 16, 17, 20]
    
    def handle(self, *args, **options):
        completed = []
        try:
            for i in self.approvals:
                try:
                    post = Post.objects.get(id=i)
                except:
                    post = None
                if post:
                    approval = PostApproval.objects.filter(post=post).first()
                    if approval and approval.approved_at:
                        self.stdout.write(f"Post {i} already approved, skipping...")
                    elif approval:
                        approval.approved_at = datetime.now()
                        approval.save()
                        completed.append(i)
                    else:
                        approval = PostApproval(post=post, approved_at=datetime.utcnow())
                        approval.save()
                        completed.append(i)
                else:
                    self.stdout.write("No post %s" % i)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR("ERROR trying to approve post. Approved: %s" % completed))
            self.stdout.write(str(e))
            return
        self.stdout.write(
            self.style.SUCCESS('Successfully approved: %s' % completed)
        )
