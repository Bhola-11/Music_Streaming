"""
Views for Moderation Queue, Report Filing, DMCA Takedown Notices & Moderator Review.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse

from .models import ModerationReport, TakedownRequest, ModerationStatus
from .forms import FileReportForm, SubmitDMCAForm
from .services import ModerationService
from music.models import Song


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)


class ModerationQueueListView(StaffRequiredMixin, ListView):
    """
    Staff portal for reviewing pending copyright, explicit content, and spam reports.
    """
    model = ModerationReport
    template_name = 'moderation/queue.html'
    context_object_name = 'reports'
    paginate_by = 30

    def get_queryset(self):
        status = self.request.GET.get('status', 'pending')
        qs = ModerationReport.objects.select_related('reporter', 'song', 'artist', 'comment')
        if status != 'all':
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')


class ModerationReportDetailView(StaffRequiredMixin, DetailView):
    """
    Detailed investigation view for a specific report with review decision actions.
    """
    model = ModerationReport
    template_name = 'moderation/report_detail.html'
    context_object_name = 'report'


class FileReportView(LoginRequiredMixin, View):
    """
    User modal/view to flag content.
    """
    template_name = 'moderation/file_report.html'

    def get(self, request, song_id):
        song = get_object_or_404(Song, id=song_id)
        form = FileReportForm()
        return render(request, self.template_name, {'form': form, 'song': song})

    def post(self, request, song_id):
        song = get_object_or_404(Song, id=song_id)
        form = FileReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.song = song
            report.save()

            messages.success(request, "Report submitted. Our trust & safety team will review the content.")
            return redirect('music:song_detail', pk=song.id)
        return render(request, self.template_name, {'form': form, 'song': song})


class SubmitTakedownRequestView(CreateView):
    """
    Formal DMCA takedown claim submission.
    """
    model = TakedownRequest
    form_class = SubmitDMCAForm
    template_name = 'moderation/file_report.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        song_id = self.kwargs.get('song_id')
        song = get_object_or_404(Song, id=song_id)
        req = form.save(commit=False)
        req.infringing_song = song
        req.save()

        # Create auto moderation report
        ModerationReport.objects.create(
            reporter=self.request.user if self.request.user.is_authenticated else None,
            reason='copyright_dmca',
            song=song,
            description=f"Formal DMCA Claim by {req.claimant_name} ({req.claimant_email}) regarding work '{req.work_title}'"
        )

        messages.success(self.request, "DMCA Notice received. Media has been queued for immediate compliance review.")
        return redirect('home')


class ExecuteModerationDecisionView(StaffRequiredMixin, View):
    """
    Approves takedown or dismisses a report.
    """
    def post(self, request, pk):
        report = get_object_or_404(ModerationReport, pk=pk)
        action = request.POST.get('action')
        notes = request.POST.get('notes', 'Reviewed by moderation staff')

        if action == 'takedown':
            ModerationService.execute_takedown(report, request.user, notes)
            messages.success(request, "Content taken down and artist notified.")
        elif action == 'dismiss':
            ModerationService.dismiss_report(report, request.user, notes)
            messages.info(request, "Report dismissed without action.")

        return redirect('moderation:queue')
