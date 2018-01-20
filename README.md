CCR
===

CCR is intended to be used as a base image for applications that rely on more
traditional configuration files or applications with very large amounts of
environment based configuration.  CCR itself is a simple python script that
renders Jinja templates from configuation data stored in Vault or from raw
environment variables.  CCR uses Python3 from a virtual environment in the
base image so as not to pollute the base image with its own Python3
dependencies.

CCR was built to leverage the large amount of existing Jinja2 templating that
already exists for our salt based application deployment strategy as we move
to a more container based deployment model.  Vault is meant to be  the secret
store for environment specific variables.  The configuration values are
expected to be stored as JSON data with key/value pairs.  Additionally the
key/value pairs can be read directly from environment variables if desired.

The default behavior of CCR is to fail if any variable referenced in the Jinja
template does not exist or has a value of None.  This behavior can be changed
if desired by using specific cli flags.

Configuration can be pulled from Vault in two ways.  The most generic way
requires passing in the Vault endpoint, role-id, secret-id, and path.  This
should work with any Vault instance that supports appid style authentication.
If you are running your image in Cloud Foundry and have a Vault instance
bound to the application the endpoint, role-id, and secret-id can be parsed
from the VCAP_SERVICES configuration by using the `--vcap` flag.  The vcap
flag expects a value of either org, space or service.  These values relate to
the broker generated Vault paths created by the HSDP Vault service and will
cause CCR to read that part of the path from the environment.  You will still
need to provide a `--path` value that will be appended to the base path
derived from VCAP_SERVICES.

Sometimes its also nice to be able to have a lot of configuration stored in
Vault and be able to override one or two values.  This is possibly by passing
in the key/value pair as an environment variable and using the
--merge-with-env flag.  Environment variables will always take precedence over
values stored in Vault.

The template flag can be passed in multiple times to render multiple templates
with a single cli command.  See ccr command line help or source code for all
command line arguments and associated help.


Templating Extras
=================
CCR provides a couple of extra funtions to templates to make converting
templates from salt-stack a bit easier.

`ccr_extras.local_addr` can be referenced inside a template and will always
return the IP address of eth0 inside the container.  This is an easy way to
replace referencing a salt grain or cross calling a salt module to retrieve the
local address when rendering templates.
```
listen_on: {{ ccr_extras.local_addr }}
```

`base64_decode` can be used as a filter to decode base64 strings that are
used to store the actual configuration value.  This can be useful for things
like certificates that may not be easily or safely stored as raw strings.
```
cert: |
    {{ cert | base64_decode }}
```


Using CCR
=========

Example entrypoint script using raw environment varibles.
```
#!/bin/sh
set -e

/ccr/ccr --from-env \
    -t /templates/my_config1.j2:/application/config/my_config1.conf \
    -t /templates/my_config2.j2:/application/config/my_config2.conf

exec /application/app_bin -c /application/config/my_config1.conf
```

Example entrypoint script using user provided Vault instances.  Endpoint,
role-id, secret-id, and path are expected to be passed into the container as
environment variables.
```
#!/bin/sh
set -e

/ccr/ccr --endpoint $endpoint \
    --role-id $role_id \
    --secret-id $secret_id \
    --path $vault_path \
    -t /templates/my_config1.j2:/application/config/my_config1.conf \
    -t /templates/my_config2.j2:/application/config/my_config2.conf

exec /application/app_bin -c /application/config/my_config1.conf
```

Example using VCAP_SERVICES environment varible to discover Vault endpoint,
secrets, and base path.
```
#!/bin/sh
set -e

/ccr/ccr --vcap service \
    --path $vault_path \
    -t /templates/my_config1.j2:/application/config/my_config1.conf \
    -t /templates/my_config2.j2:/application/config/my_config2.conf

exec /application/app_bin -c /application/config/my_config1.conf
```

Example using VCAP_SERVICES environment variable for Vault discover and
merging other local environment variables before rendering templates.
```
#!/bin/sh
set -e

/ccr/ccr --vcap service \
    --path $vault_path \
    --merge-with-env \
    -t /templates/my_config1.j2:/application/config/my_config1.conf \
    -t /templates/my_config2.j2:/application/config/my_config2.conf

exec /application/app_bin -c /application/config/my_config1.conf
```

