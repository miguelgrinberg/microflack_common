"""Replacement requests functions.

The get(), post(), put() and delete() functions in this module can be used as
a drop-in replacement for the ones in python-requests. These functions
optionally accept relative URLs (for example /api/users), which are sent to
the load balancer configured for the service. The functions also implement
retries.
"""
import os

from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util import Retry

_session = None


def _get_requests_session():
    global _session
    if _session is None:
        _session = Session()

        # configure 5 retries for any requests that return 502 or 503 errors
        # exponential backoff increases the delay for each retry iteration
        _session.mount('https://', HTTPAdapter(max_retries=Retry(
            total=5, backoff_factor=0.1, status_forcelist=[502, 503])))
        _session.mount('http://', HTTPAdapter(max_retries=Retry(
            total=5, backoff_factor=0.1, status_forcelist=[502, 503])))
    return _session


def _make_request(method, url, *args, **kwargs):
    if '://' not in url:
        url = os.environ['LB'] + url
    raise_for_status = kwargs.pop('raise_for_status', True)

    response = getattr(_get_requests_session(), method.lower())(
        url, *args, **kwargs)
    if raise_for_status:
        response.raise_for_status()
    return response


def get(url, *args, **kwargs):
    """Send a GET request.

    :param url the target URL. If the URL does not include the scheme, host
               and port, the request is sent to the load balancer used by the
               application.
    :param raise_for_status if set to True, the raise_for_status() method is
                            invoked on the response. By default this argument
                            is set to False.

    The positional and keyword arguments are sent to the requests package. The
    response from requests is returned.
    """
    return _make_request('get', url, *args, **kwargs)


def post(url, *args, **kwargs):
    """Send a POST request.

    :param url the target URL. If the URL does not include the scheme, host
               and port, the request is sent to the load balancer used by the
               application.
    :param raise_for_status if set to True, the raise_for_status() method is
                            invoked on the response. By default this argument
                            is set to False.

    Any other positional and keyword arguments are sent to the requests
    package. The response from requests is returned.
    """
    return _make_request('post', url, *args, **kwargs)


def put(url, *args, **kwargs):
    """Send a PUT request.

    :param url the target URL. If the URL does not include the scheme, host
               and port, the request is sent to the load balancer used by the
               application.
    :param raise_for_status if set to True, the raise_for_status() method is
                            invoked on the response. By default this argument
                            is set to False.

    Any other positional and keyword arguments are sent to the requests
    package. The response from requests is returned.
    """
    return _make_request('put', url, *args, **kwargs)


def delete(url, *args, **kwargs):
    """Send a DELETE request.

    :param url the target URL. If the URL does not include the scheme, host
               and port, the request is sent to the load balancer used by the
               application.
    :param raise_for_status if set to True, the raise_for_status() method is
                            invoked on the response. By default this argument
                            is set to False.

    Any other positional and keyword arguments are sent to the requests
    package. The response from requests is returned.
    """
    return _make_request('delete', url, *args, **kwargs)
