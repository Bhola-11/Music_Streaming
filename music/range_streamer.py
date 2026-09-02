import io
import wave
import struct
import math
import os
import re
from django.http import HttpResponse, StreamingHttpResponse, Http404


def generate_synth_audio_bytes(duration: int = 30, bpm: int = 124) -> bytes:
    """
    Generates in-memory stereo 44.1kHz 16-bit WAV synth audio as a master stream fallback.
    """
    sample_rate = 44100
    n_samples = int(sample_rate * min(60, max(10, duration)))
    buf = io.BytesIO()

    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            beat = (i * bpm / (60 * sample_rate))
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * beat)

            # Rich layered chord (F# minor / Synthwave harmonics)
            val_l = (0.22 * math.sin(2 * math.pi * 185.0 * t) +
                     0.20 * math.sin(2 * math.pi * 220.0 * t) +
                     0.18 * math.sin(2 * math.pi * 277.18 * t) * pulse +
                     0.12 * math.sin(2 * math.pi * 329.63 * t))

            val_r = (0.22 * math.sin(2 * math.pi * 185.0 * t) +
                     0.18 * math.sin(2 * math.pi * 220.0 * t) * pulse +
                     0.20 * math.sin(2 * math.pi * 277.18 * t) +
                     0.12 * math.sin(2 * math.pi * 369.99 * t))

            env = min(1.0, t / 0.3) * min(1.0, ((n_samples / sample_rate) - t) / 0.5)
            sample_l = int(max(-32767, min(32767, val_l * env * 26000)))
            sample_r = int(max(-32767, min(32767, val_r * env * 26000)))
            frames.extend(struct.pack('<hh', sample_l, sample_r))

        wav_file.writeframes(frames)
    buf.seek(0)
    return buf.getvalue()


class RangeBytesWrapper:
    """
    Bytes iterator for in-memory buffer streaming.
    """
    def __init__(self, data: bytes, offset: int = 0, length: int = None, chunk_size: int = 65536):
        self.data = data
        self.offset = offset
        self.remaining = length if length is not None else (len(data) - offset)
        self.chunk_size = chunk_size

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining <= 0 or self.offset >= len(self.data):
            raise StopIteration
        chunk_len = min(self.chunk_size, self.remaining)
        chunk = self.data[self.offset : self.offset + chunk_len]
        self.offset += len(chunk)
        self.remaining -= len(chunk)
        return chunk


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


def get_range_response(request, file_path: str = None, content_type: str = 'audio/mpeg', duration: int = 30) -> HttpResponse:
    """
    Constructs an HTTP 206 Partial Content or HTTP 200 OK stream response.
    Gracefully falls back to procedural synth audio if the local master file does not exist.
    """
    if file_path and os.path.exists(file_path):
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
    else:
        # Fallback to procedural synth audio stream
        audio_bytes = generate_synth_audio_bytes(duration=duration)
        total_len = len(audio_bytes)
        range_header = request.META.get('HTTP_RANGE', '').strip()
        range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

        if range_match:
            first_byte, last_byte = range_match.groups()
            first_byte = int(first_byte)
            last_byte = int(last_byte) if last_byte else total_len - 1
            length = last_byte - first_byte + 1

            response = StreamingHttpResponse(
                RangeBytesWrapper(audio_bytes, offset=first_byte, length=length),
                status=206,
                content_type='audio/wav'
            )
            response['Content-Length'] = str(length)
            response['Content-Range'] = f"bytes {first_byte}-{last_byte}/{total_len}"
        else:
            response = StreamingHttpResponse(
                RangeBytesWrapper(audio_bytes, offset=0, length=total_len),
                status=200,
                content_type='audio/wav'
            )
            response['Content-Length'] = str(total_len)

        response['Accept-Ranges'] = 'bytes'
        response['Cache-Control'] = 'private, max-age=3600'
        return response

