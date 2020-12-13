from django import forms
from django.contrib import admin
from .models import Post, Vote, Client, Suggestion


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    pass


class ClientForm(forms.ModelForm):

    ip = forms.CharField(required=True)

    def save(self, commit=True):
        addr = Client.aton(self.cleaned_data.get("ip"))
        self.instance.ip_address = addr
        return self.instance

    def save_m2m(self):
        # FIXME: this function is required by ModelAdmin, otherwise save process will fail
        pass

    class Meta:
        model = Client
        fields = ['ip']


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientForm
    exclude = ("ip_address",)
    list_display = ("ip",)

    def ip(self, obj):
        return Client.ntoa(obj.ip_address)


@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    pass
