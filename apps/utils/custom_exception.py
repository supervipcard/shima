from django.core.exceptions import PermissionDenied
from django.http import Http404

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import set_rollback


def custom_get_full_details(detail):
    if isinstance(detail, list):
        return [custom_get_full_details(item) for item in detail][0]
    elif isinstance(detail, dict):
        return [custom_get_full_details(value) for key, value in detail.items()][0]
    return {
        'message': detail,
        'code': detail.code
    }


def custom_exception_handler(exc, context):
    """
    Returns the response that should be used for any given exception.

    By default we handle the REST framework `APIException`, and also
    Django's built-in `Http404` and `PermissionDenied` exceptions.

    Any unhandled exceptions may return `None`, which will cause a 500 error
    to be raised.
    """
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    if isinstance(exc, exceptions.APIException):
        headers = {}
        if getattr(exc, 'auth_header', None):
            headers['WWW-Authenticate'] = exc.auth_header
        if getattr(exc, 'wait', None):
            headers['Retry-After'] = '%d' % exc.wait

        data = custom_get_full_details(exc.detail)

        set_rollback()
        return Response(data, status=exc.status_code, headers=headers)

    return None
