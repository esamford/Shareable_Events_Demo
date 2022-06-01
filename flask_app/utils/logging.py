from flask_app.models.client_ip_address import ClientIPAddress
from flask_app.models.security_log import SecurityLog


def log_security_issue(client_ip: str, log_type: str):
    # Log failed logins.
    client_ip_address = ClientIPAddress.get_by_ip_address(client_ip)
    if client_ip_address is None:
        client_ip_address = ClientIPAddress.get_by_id(ClientIPAddress.create(client_ip))
    new_data = {
        'client_ip_address_id': client_ip_address.id,
        'log_type': log_type,
    }
    SecurityLog.create(new_data)
