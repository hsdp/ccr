#!/ccr/ccr.d/bin/python3

import os
import sys
import json
import socket
import base64
import argparse
import hvac
from jinja2.exceptions import UndefinedError
from jinja2 import Environment, StrictUndefined, meta


class CcrExtras(object):

    def __init__(self):
        self.local_addr = socket.gethostbyname(socket.gethostname())
        self.loopback_addr = '127.0.0.1'


class JinjaEnv(object):

    allow_undefined = False

    @classmethod
    def get_env(cls):
        if cls.allow_undefined:
            env = Environment()
        else:
            env = Environment(undefined=StrictUndefined)
        env.globals['ccr_extras'] = CcrExtras()
        env.filters['b64decode'] = lambda x: base64.b64decode(x).decode()
        return env


def get_vcap_credentials(service_name='hsdp-vault'):
    vcap_services = os.getenv('VCAP_SERVICES', None)
    if vcap_services:
        vcap_services = json.loads(vcap_services)
    else:
        print('ERROR: VCAP_SERVICES does not exist.')
        sys.exit(1)
    if service_name not in vcap_services:
        print('ERROR: Vault service instance does not exist.')
        sys.exit(1)
    service_instance = vcap_services.get(service_name)
    for item in service_instance:
        if 'credentials' in item:
            credentials = item.get('credentials')
            break
    else:
        raise EnvironmentError('Credentials missing in VCAP_SERVICES.')
    return credentials


def get_vault_secrets(url, path, role_id, secret_id):
    client = hvac.Client(url=url)
    _ = client.auth_approle(role_id, secret_id)
    data = client.read(path)
    if not isinstance(data['data'], dict):
        print('ERROR: Vault data is not a JSON dictionary!')
        sys.exit(1)
    return data['data']


def get_secrets_from_env(templates):
    secrets = {}
    for template in templates:
        try:
            filename = template.split(':')[0]
            jinja_string = open(filename).read()
        except IOError:
            print("ERROR: Could not open file {0}.  Exiting.".format(filename))
            sys.exit(1)
        template_vars = meta.find_undeclared_variables(
            JinjaEnv.get_env().parse(jinja_string)
        )
        for var in template_vars:
            if var in os.environ:
                secrets[var] = os.getenv(var)
    return secrets


def check_null(secrets):
    null_values = [k for (k, v) in secrets.items() if v is None]
    if null_values:
        print('ERROR: The following variables have None values: '
              '{0}.  Exiting.').format(",".join(null_values))
        sys.exit(1)


def render_templates(templates, secrets):
    for template in templates:
        source, destination = template.split(':')
        try:
            with open(source, 'r') as s:
                with open(destination, 'w') as d:
                    d.write(JinjaEnv.get_env().from_string(
                        s.read()).render(**secrets))
        except IOError:
            print('ERROR: Unable to access {0}. Exiting.'.format(source))
            sys.exit(1)
        except UndefinedError as undefined:
            print('ERROR: {0}'.format(undefined.message))
            sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--from-env',
        dest='from_env',
        action='store_true',
        help=('This will expect template data to be passed in via raw '
              'envionment variables.  The templates will be inspected for '
              'variables and the variable names will be expected to exist as '
              'environment variables.  This configuration is useful for '
              'development environments where Vault may not be accessible '
              'from.')
    )
    group.add_argument(
        '--vcap',
        dest='vcap',
        choices=['org', 'space', 'service'],
        help=('Use this argument if you are running an application in Cloud '
              'Foundry and have bound a brokered service instance to the '
              'app.  This argument will cause render-configs to read the '
              'VCAP_SERVICES envionment variable to discover the Vault '
              'endpoints and secrets.  One of the following choices is '
              'required for this argument: org, space, service.  These '
              'choices relate to the broker created vault paths.  The '
              'value provided to --path will be appended to this to define '
              'the vault key to pull data from.')
    )
    group.add_argument(
        '--endpoint',
        dest='endpoint',
        help=('Specify the Vault endpoint manually with this argument.  If '
              'this argument is used --role-id, --secret-id, and --path '
              'are also required arguments.')
    )
    parser.add_argument(
        '--role-id',
        dest='role_id',
        help='The Vault appauth role-id to authenticate to Vault with.'
    )
    parser.add_argument(
        '--secret-id',
        dest='secret_id',
        help='The Vault appauth secret-id to authenticate to Vault with.'
    )
    parser.add_argument(
        '--path',
        dest='path',
        help=('The vault path to use for config data.  If you are using the '
              '--vcap arg the value for this should be the path without the '
              'brokered created path.  This will be appended to the broker '
              'created path.  If you are using the --endpoint arg this will '
              'need to be the full vault path you are using.')
    )
    parser.add_argument(
        '-t',
        '--template',
        dest='template',
        action='append',
        help=('This argument can be used multiple time to render multiple '
              'files.  The templates are expected to exist on the local '
              'filesystem.  An example value for this would be '
              '`/app/templates/app.cfg:/app/config/app.cfg`.  The values for '
              'the template and the final file should be delimited with a '
              '`:`.')
    )
    parser.add_argument(
        '--allow-undefined',
        dest='allow_undefined',
        action='store_true',
        default=False,
        help=('This option will allow templates to be rendered even if there '
              'are undefined variables in the templates.  The default '
              'behavior is to fail when undefined variables are encountered.')
    )
    parser.add_argument(
        '--allow-null',
        dest='allow_null',
        action='store_true',
        help=('By default variables that have values that result in a Python '
              'value of `None` are not allowed.  Typically this will get cast '
              'to a string and rendered as `None` into a configuration file.  '
              'When templates are rendered all variables are checked to '
              'ensure the value is something other than None.  If a None '
              'value is found an error will be throw.  Setting this flag will '
              'allow for None values.')
    )
    parser.add_argument(
        '--merge-with-env',
        dest='merge_with_env',
        action='store_true',
        help=('Setting this flag will cause ccr to merge Vault based '
              'variables with environment variables before rendering files.  '
              'If the same variable exists in both Vault and environment '
              'variables then environment will take precedence.  This flag is '
              'ignored if used with `--from-env`.  Only variables that are '
              'discovered in templates will be merged in.')
    )
    parser.add_argument(
        '--vault-to-env',
        dest='vault_to_env',
        action='store_true',
        help=('This flag will cuase CCR to pull secrets from Vault and create '
              'environment variables from the result.  Data is assumed to be '
              'JSON key/value string pairs in Vault.')
    )
    parser.add_argument(
        '--out-file',
        dest='out_file',
        default='/dev/shm/environment',
        help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if args.endpoint:
        if args.role_id is None or args.secret_id is None or args.path is None:
            msg = '--endpoint requires --role-id --secret-id and --path'
            parser.error(msg)
    if args.vcap:
        if args.path is None:
            parser.error('--vcap requires --path')
        else:
            creds = get_vcap_credentials()
            args.endpoint = creds['endpoint']
            vcap_path = creds[''.join([args.vcap, '_secret_path'])]
            args.path = '/'.join(
                '/'.join([vcap_path, args.path]).split('/')[2:])
            args.role_id = creds['role_id']
            args.secret_id = creds['secret_id']
    return args


def main():
    args = parse_args()
    JinjaEnv.allow_undefined = args.allow_undefined
    if args.from_env:
        secrets = get_secrets_from_env(args.template)
    elif args.endpoint or args.vcap:
        secrets = get_vault_secrets(
            url=args.endpoint,
            path=args.path,
            role_id=args.role_id,
            secret_id= args.secret_id
        )
        if args.merge_with_env:
            secrets.update(get_secrets_from_env(args.template))
        if not args.allow_null:
            check_null(secrets)
    if args.vault_to_env:
        with open(args.out_file, 'w') as f:
            for k, v in secrets.items():
                f.write('export {0}={1}\n'.format(k, v))
    else:
        render_templates(args.template, secrets)


if __name__ == '__main__':
    main()
