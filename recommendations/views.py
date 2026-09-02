from django.views.generic import TemplateView

class RecommendationsFeedView(TemplateView):
    template_name = 'recommendations/feed.html'
