from flask import request


def get_client_ip_from_client_request(r: request) -> str:
    """
    :param r: The HTTP request from the client.
    :return: The IP address of the client.
    """
    return str(r.environ['REMOTE_ADDR'])


def get_client_ip_from_proxy_request(r: request) -> str:
    """
    :param r: The HTTP request from the client.
    :return: The IP address of the client. According to the source below, this
        should still get the client's IP address even if they use a proxy server.
        Source: https://stackabuse.com/how-to-get-users-ip-address-using-flask/
    """
    return str(r.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr))


def get_client_ip(r: request) -> str:
    try:
        return get_client_ip_from_proxy_request(r)
    except Exception:
        return get_client_ip_from_client_request(r)

