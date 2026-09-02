from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class ModerationQueueView(LoginRequiredMixin, TemplateView):
    template_name = 'moderation/queue.html'
