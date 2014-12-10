from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from smartmin.views import SmartTemplateView


class HomeView(SmartTemplateView):
    """
    Our homepage.
    """
    template_name = 'home/home.haml'

    def pre_process(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(reverse('users.user_login'))

        return super(HomeView, self).pre_process(request)