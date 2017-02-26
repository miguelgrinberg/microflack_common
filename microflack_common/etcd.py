import os

import etcd


def etcd_client(**kwargs):
    """Return an etcd client instance.

    This function returns an etcd client instance initialized with all the
    available etcd endpoints configured in the ETCD environment variable.
    """
    if 'host' not in kwargs:
        if 'ETCD' not in os.environ:
            raise RuntimeError('etcd service has not been configured.')

        # parse the etcd host list from the environment
        etcd_hosts = tuple()
        for url in [u.strip() for u in os.environ['ETCD'].split(',')]:
            if not url.startswith('http://'):
                raise ValueError('Only http is supported for etcd')
            host, port = url[7:].split(':', 1)
            etcd_hosts += ((host, int(port)),)

        kwargs['host'] = etcd_hosts

    if 'allow_reconnect' not in kwargs:
        kwargs['allow_reconnect'] = True

    # open a client session with etcd
    return etcd.Client(**kwargs)
