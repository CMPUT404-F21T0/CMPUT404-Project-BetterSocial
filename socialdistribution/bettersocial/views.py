from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from django.views import generic


class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'
    context_object_name = 'user_list'

    # TODO: Not sure if this is the proper way to query all users / users post in db
    def users(self):
        return User.objects.all()



@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'
