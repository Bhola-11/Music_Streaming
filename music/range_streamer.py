"""
HTTP 206 Partial Content Range Streaming Engine.
Provides byte-range audio streaming for low-latency scrubbing and seek operations.
"""
import os
import re
from django.http import HttpResponse, StreamingHttpResponse, Http404


class RangeFileWrapper:
    """
    File iterator chunking byte segments for HTTP partial content responses.
    """
    def __init__(self, file_handle, offset: int = 0, length: int = None, chunk_size: int = 65536):
        self.file_handle = file_handle
        self.offset = offset
        self.remaining = length
        self.chunk_size = chunk_size
        self.file_handle.seek(self.offset, os.SEEK_SET)

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is not None and self.remaining <= 0:
            raise StopIteration
        
        read_size = self.chunk_size
        if self.remaining is not None:
            read_size = min(read_size, self.remaining)
        
        data = self.file_handle.read(read_size)
        if not data:
            raise StopIteration
        
        if self.remaining is not None:
            self.remaining -= len(data)
        return data


def get_range_response(request, file_path: str, content_type: str = 'audio/mpeg') -> HttpResponse:
    """
    Constructs an HTTP 206 Partial Content or HTTP 200 OK stream response.
    """
    if not os.path.exists(file_path):
        raise Http404("Audio master file does not exist on storage.")

    file_size = os.path.getsize(file_path)
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte)
        last_byte = int(last_byte) if last_byte else file_size - 1

        if first_byte >= file_size or last_byte >= file_size:
            response = HttpResponse(status=416)
            response['Content-Range'] = f"bytes */{file_size}"
            return response

        length = last_byte - first_byte + 1
        file_obj = open(file_path, 'rb')
        response = StreamingHttpResponse(
            RangeFileWrapper(file_obj, offset=first_byte, length=length),
            status=206,
            content_type=content_type
        )
        response['Content-Length'] = str(length)
        response['Content-Range'] = f"bytes {first_byte}-{last_byte}/{file_size}"
    else:
        # Full content
        file_obj = open(file_path, 'rb')
        response = StreamingHttpResponse(
            RangeFileWrapper(file_obj, offset=0, length=file_size),
            status=200,
            content_type=content_type
        )
        response['Content-Length'] = str(file_size)

    response['Accept-Ranges'] = 'bytes'
    response['Cache-Control'] = 'private, max-age=3600'
    return response
