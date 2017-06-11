import os
import socket
import time

import docker

from microflack_common.etcd import etcd_client

docker_attrs = None


def is_dockerized():
    """Return True if the application is running in a Docker container."""
    return os.path.exists('/.dockerenv')


def get_docker_attributes():
    """Return Docker attributtes for this container.

    This is done through the Docker API. The purpose is for a container to
    be able to find information about itself, such as what external port in
    the host was allocated to it.
    """
    global docker_attrs
    if docker_attrs:
        return docker_attrs
    docker_client = docker.from_env()
    container = docker_client.containers.get(socket.gethostname())
    if not container:
        raise RuntimeError('Cannot obtain docker attributtes')
    docker_attrs = container.attrs
    return docker_attrs


def get_service_name():
    """Return the name of this service.

    This name is provided in the environment variable SERVICE_NAME.
    """
    if 'SERVICE_NAME' in os.environ:
        return os.environ['SERVICE_NAME']
    raise RuntimeError('Cannot determine service name')


def get_instance_name():
    """Return the name of this instance.

    The name can be passed in the environment as INSTANCE_NAME, or else it is
    constructed from the SERVICE_NAME and SERVICE_VERSION variables. If
    running inside Docker, the hostname of the container is appended to the
    name.
    """
    instance_name = ''
    if 'INSTANCE_NAME' in os.environ:
        instance_name = os.environ['INSTANCE_NAME']
    elif 'SERVICE_NAME' in os.environ:
        instance_name = os.environ['SERVICE_NAME']
        if 'SERVICE_VERSION' in os.environ:
            instance_name += '_v' + os.environ['SERVICE_VERSION']
    if not is_dockerized():
        if not instance_name:
            raise RuntimeError('Cannot determine instance name')
        return instance_name
    return instance_name + '_' + socket.gethostname()


def get_service_address():
    """Return the listen address of this service.

    This can be passed in the SERVICE_ADDRESS environment variable, but when
    running as a Docker container, if the variable isn't given the address
    returned is the address that other containers can use to connect.
    """
    if 'SERVICE_ADDRESS' in os.environ:
        return os.environ['SERVICE_ADDRESS']
    if not is_dockerized():
        raise RuntimeError('Cannot determine service name')
    attrs = get_docker_attributes()
    ip_address = os.environ.get('HOST_IP_ADDRESS',
                                attrs['NetworkSettings']['Gateway'])
    port = list(attrs['NetworkSettings']['Ports'].values())[0][0]['HostPort']
    return '{}:{}'.format(ip_address, port)


def get_service_url():
    """Return the root URL of this service."""
    if 'SERVICE_URL' in os.environ:
        return os.environ['SERVICE_URL']
    # the default location for each service is /api/<service>
    return '/api/{}'.format(get_service_name())


def register():
    """Register this service with the system.

    The registration has a ttl of 50s, and is refreshed every 15s, so it can
    fail up to 3 times before the service is dropped.
    """
    service_name = get_service_name()
    instance_name = get_instance_name()
    service_address = get_service_address()
    load_balancer = os.environ.get('LOAD_BALANCER', 'haproxy')
    balance_algorithm = os.environ.get('LB_ALGORITHM', 'roundrobin')

    # open a client session with etcd
    etcd = etcd_client()

    while True:
        try:
            if load_balancer == 'traefik':
                # service registration for the traefik load balancer
                backend = '/traefik/backends/{}-backend/servers/{}/url'.format(
                    service_name, instance_name)
                etcd.write(backend + '/url', 'http://' + service_address,
                           ttl=50)
                etcd.write(backend + '/weight', '1', ttl=50)
                if balance_algorithm == 'source':
                    etcd.write('/traefik/backends/{}-backend/loadbalancer'
                               '/sticky'.format(service_name), 'true')
                else:
                    etcd.write('/traefik/backends/{}-backend/loadbalancer'
                               '/sticky'.format(service_name), 'false')

                frontend = '/traefik/frontends/{}-frontend'.format(
                    service_name)
                etcd.write(frontend + '/backend', service_name + '-backend',
                           ttl=50)
                etcd.write(frontend + '/entrypoints', 'http', ttl=50)
                etcd.write(frontend + '/routes/path/rule',
                           'PathPrefix:' + get_service_url(), ttl=50)
            else:
                # service registration for the haproxy load balancer
                etcd.write('/services/{}/location'.format(service_name),
                           get_service_url())
                etcd.write('/services/{}/backend/balance'.format(service_name),
                           balance_algorithm)
                etcd.write('/services/{}/upstream/{}'.format(service_name,
                                                             instance_name),
                           service_address, ttl=50)
        except:
            # we had a failure, hopefully we'll get it next time
            pass
        time.sleep(15)
