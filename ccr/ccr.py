#!/ccr/ccr.d/bin/python3

import os
import sys
import socket
import base64
import argparse
from jinja2.exceptions import UndefinedError
from jinja2 import Environment, StrictUndefined, meta
import ccr_vault


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


def render_template(template, secrets, undefined=False):
    return JinjaEnv.get_env().from_string(template).render(**secrets)


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


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
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
        required=True,
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
    args = parser.parse_args()
    if args.endpoint:
        if args.role_id is None or args.secret_id is None or args.path is None:
            msg = '--endpoint requires --role-id --secret-id and --path'
            parser.error(msg)
    if args.vcap:
        if args.path is None:
            parser.error('--vcap requires --path')
    return args


def main():
    args = parse_args()
    JinjaEnv.allow_undefined = args.allow_undefined
    if args.from_env:
        secrets = get_secrets_from_env(args.template)
    else:
        creds = {'url': None, 'path': None, 'role_id': None, 'secret_id': None}
        if args.endpoint:
            creds['url'] = args.endpoint
            creds['path'] = args.path
            creds['role_id'] = args.role_id
            creds['secret_id'] = args.secret_id
        elif args.vcap:
            vcap_creds = ccr_vault.get_vault_credentials()
            vcap_path = vcap_creds[''.join([args.vcap, '_secret_path'])]
            path = '/'.join('/'.join([vcap_path, args.path]).split('/')[2:])
            creds['url'] = vcap_creds['endpoint']
            creds['path'] = path
            creds['role_id'] = vcap_creds['role_id']
            creds['secret_id'] = vcap_creds['secret_id']
        secrets = ccr_vault.get_vault_secret(**creds)
        if args.merge_with_env:
            secrets.update(get_secrets_from_env(args.template))
    if not args.allow_null:
        null_values = [k for (k,v) in secrets.items() if v is None]
        if null_values:
            print('ERROR: The following variables have None values: '
                  '{0}.  Exiting.').format(",".join(null_values))
            sys.exit(1)
    for templates in args.template:
        template, filename = templates.split(':')
        try:
            with open(template, 'r') as t:
                with open(filename, 'w') as f:
                    f.write(render_template(t.read(), secrets))
        except IOError:
            print('ERROR: Unable to access {0}. Exiting.'.format(template))
            sys.exit(1)
        except UndefinedError as undefined:
            print('ERROR: {0}'.format(undefined.message))
            sys.exit(1)


if __name__ == '__main__':
    main()
