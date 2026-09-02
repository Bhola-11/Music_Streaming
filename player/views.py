from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

class SyncPlaybackStateView(LoginRequiredMixin, View):
    def post(self, request):
        return JsonResponse({'status': 'synced'})
