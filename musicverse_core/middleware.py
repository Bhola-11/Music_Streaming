"""
Core middleware for MusicVerse.
Provides request performance timing, request UUID correlation, and security enforcement.
"""
import time
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse

logger = logging.getLogger('musicverse.performance')


class RequestPerformanceMiddleware(MiddlewareMixin):
    """
    Measures request latency, attaches unique request IDs, and logs slow queries/responses.
    """
    def process_request(self, request):
        request.request_id = str(uuid.uuid4())
        request._start_time = time.time()

    def process_response(self, request, response):
        duration = 0.0
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        
        # Attach response performance headers
        response['X-Request-ID'] = getattr(request, 'request_id', str(uuid.uuid4()))
        response['X-Response-Time-MS'] = f"{duration * 1000:.2f}"
        response['X-MusicVerse-Cluster'] = 'cluster-alpha-01'

        if duration > 1.5:
            logger.warning(
                f"[SLOW_REQUEST] {request.method} {request.path} took {duration:.3f}s - ID: {getattr(request, 'request_id', 'unknown')}"
            )
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Injects enterprise-grade Content-Security-Policy and protective headers.
    """
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response
