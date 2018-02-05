import sys
import json
import hvac


def get_vault_credentials(service_name='hsdp-vault'):
    vcap_services = json.loads(os.getenv('VCAP_SERVICES', None))
    if not vcap_services:
        raise EnvironmentError('VCAP_SERVICES does not exist.')
    if service_name not in vcap_services:
        raise EnvironmentError('Vault service instance does not exist.')
    service_instance = vcap_services.get(service_name)
    for item in service_instance:
        if 'credentials' in item:
            credentials = item.get('credentials')
            break
    else:
        raise EnvironmentError('Credentials missing in VCAP_SERVICES.')
    return credentials


def get_vault_secret(url, path, role_id, secret_id):
    client = hvac.Client(url=url)
    _ = client.auth_approle(role_id, secret_id)
    data = client.read(path)
    if not isinstance(data['data'], dict):
        print('ERROR: Vault data is not a JSON dictionary!')
        sys.exit(1)
    return data['data']
