from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from .models import Playlist

class PlaylistListView(ListView):
    model = Playlist
    template_name = 'playlists/playlist_list.html'
    context_object_name = 'playlists'

class PlaylistDetailView(DetailView):
    model = Playlist
    template_name = 'playlists/playlist_detail.html'
    context_object_name = 'playlist'
