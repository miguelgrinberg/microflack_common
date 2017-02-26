"""Common unit testing helpers."""
import base64
import json
import unittest


class FlackTestCase(unittest.TestCase):
    """A TestCase subclass with common functionality used by MicroFlack
    services.
    """
    def get_headers(self, basic_auth=None, token_auth=None):
        """Return the headers to include in the request."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if basic_auth is not None:
            headers['Authorization'] = 'Basic ' + base64.b64encode(
                basic_auth.encode('utf-8')).decode('utf-8')
        if token_auth is not None:
            headers['Authorization'] = 'Bearer ' + token_auth
        return headers

    def get(self, url, basic_auth=None, token_auth=None):
        """Send a GET request through the Flask test client."""
        rv = self.client.get(url,
                             headers=self.get_headers(basic_auth, token_auth))
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def post(self, url, data=None, basic_auth=None, token_auth=None):
        """Send a POST request through the Flask test client."""
        d = data if data is None else json.dumps(data)
        rv = self.client.post(url, data=d,
                              headers=self.get_headers(basic_auth, token_auth))
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def put(self, url, data=None, basic_auth=None, token_auth=None):
        """Send a PUT request through the Flask test client."""
        d = data if data is None else json.dumps(data)
        rv = self.client.put(url, data=d,
                             headers=self.get_headers(basic_auth, token_auth))
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers

    def delete(self, url, basic_auth=None, token_auth=None):
        """Send a DELETE request through the Flask test client."""
        rv = self.client.delete(url, headers=self.get_headers(basic_auth,
                                                              token_auth))
        body = rv.get_data(as_text=True)
        if body is not None and body != '':
            try:
                body = json.loads(body)
            except:
                pass
        return body, rv.status_code, rv.headers
