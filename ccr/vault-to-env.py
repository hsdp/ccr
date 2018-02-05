import argparse
import ccr_vault


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
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


if __name__ == '__main__':
    main()
