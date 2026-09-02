"""
Artist Services: Royalty Calculation, Verification Processing & Discography Analytics.
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from .models import Artist, RoyaltyStatement, ArtistVerificationRequest, VerificationStatus
from music.models import Song
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class RoyaltyCalculatorService:
    """
    Computes streaming royalties for artists based on playback metrics.
    """
    DEFAULT_STREAM_RATE = Decimal('0.0045')  # $0.0045 per stream
    PLATFORM_FEE_PERCENT = Decimal('0.15')   # 15% platform infrastructure fee

    @classmethod
    def generate_monthly_statement(cls, artist: Artist, start_date, end_date) -> RoyaltyStatement:
        """
        Calculates streams across artist tracks and generates a locked royalty statement.
        """
        songs = Song.objects.filter(artist=artist)
        total_plays = songs.aggregate(total=Sum('play_count'))['total'] or 0

        rate = artist.royalty_split_rate or cls.DEFAULT_STREAM_RATE
        gross_earnings = Decimal(total_plays) * rate
        platform_fee = gross_earnings * cls.PLATFORM_FEE_PERCENT
        net_payable = gross_earnings - platform_fee

        statement = RoyaltyStatement.objects.create(
            artist=artist,
            period_start=start_date,
            period_end=end_date,
            total_streams=total_plays,
            gross_earnings_usd=gross_earnings,
            platform_fee_usd=platform_fee,
            net_payable_usd=net_payable,
            is_paid=False
        )

        # Update artist unpaid balance
        artist.unpaid_balance += net_payable
        artist.save(update_fields=['unpaid_balance'])

        return statement


class VerificationService:
    """
    Manages artist blue-badge verification approval / rejection workflows.
    """

    @classmethod
    def approve_verification(cls, verification_request: ArtistVerificationRequest, reviewer_user) -> bool:
        verification_request.status = VerificationStatus.VERIFIED
        verification_request.reviewed_by = reviewer_user
        verification_request.reviewed_at = timezone.now()
        verification_request.save()

        artist = verification_request.artist
        artist.verification_status = VerificationStatus.VERIFIED
        artist.verified_at = timezone.now()
        artist.save(update_fields=['verification_status', 'verified_at'])

        AuditService.log_admin_action(
            admin_user=reviewer_user,
            action='artist.verification_approved',
            target_entity=f"Artist:{artist.name}",
            justification_reason="Approved official identity documentation."
        )
        return True

    @classmethod
    def reject_verification(cls, verification_request: ArtistVerificationRequest, reviewer_user, reason: str) -> bool:
        verification_request.status = VerificationStatus.REJECTED
        verification_request.reviewed_by = reviewer_user
        verification_request.reviewed_at = timezone.now()
        verification_request.rejection_reason = reason
        verification_request.save()

        artist = verification_request.artist
        artist.verification_status = VerificationStatus.REJECTED
        artist.save(update_fields=['verification_status'])

        AuditService.log_admin_action(
            admin_user=reviewer_user,
            action='artist.verification_rejected',
            target_entity=f"Artist:{artist.name}",
            justification_reason=reason
        )
        return True
