from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views import generic


class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'
