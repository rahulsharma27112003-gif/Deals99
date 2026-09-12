import threading

_thread_locals = threading.local()


def get_current_user():
    return getattr(_thread_locals, 'user', None)


def get_current_request():
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    """Middleware that saves the current request and user in thread local storage.

    This allows signal handlers to attribute changes to the acting user when available.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            _thread_locals.request = request
            _thread_locals.user = getattr(request, 'user', None)
            response = self.get_response(request)
            return response
        finally:
            # Clean up
            _thread_locals.request = None
            _thread_locals.user = None