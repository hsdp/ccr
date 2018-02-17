CCR
===

CCR is intended to be used as a base image for applications that rely on more
traditional configuration files or applications with very large amounts of
environment based configuration.  CCR is a simple python script that renders
Jinja templates from configuation data stored in Vault or environment
variables.  In addition to being able to render config templates, CCR can also
be used to write out an environment file that can be sourced in an entrypoint
script for applications that expect configuration to be provided as environment
variables.  Either mode expects the source variables to be stored in Vault.
CCR uses Python3 from a virtual environment in the base image to prevent
polluting the base image with its own dependencies.


Jinja Templating
================

CCR expects configuration templates to use the Jinja2 templating language.
The primary reason for choosing Jinja2 was to ease migrating from saltstack
based deployments to container based deployments.

Template variables can be pulled from Vault, environment variables or both in
order to render the templates into the final configuration file.

The default behavior of CCR is to fail if any variable referenced in the Jinja
template does not exist or has a value of None.  This behavior can be changed
if desired by using specific cli flags.

Sometimes its also nice to be able to have a lot of configuration stored in
Vault and be able to override one or two values.  This is possible by passing
in the key/value pair as an environment variable and using the
`--merge-with-env` flag.  Environment variables will always take precedence
over values stored in Vault.

The template flag can be passed in multiple times to render multiple templates
with a single cli command.

See ccr command line help or source code for all command line arguments and
associated help.


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

Using Vault with CCR
====================
The configuration values are expected to be stored as JSON key/value pairs in
Vault.  Configuration can be pulled from Vault in two ways.  The most generic
way requires passing in the Vault endpoint, role-id, secret-id, and path.  This
should work with any Vault instance that supports appid style authentication.

**Example entrypoint script using user provided config:**
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

If you are running your image in Cloud Foundry and have a Vault service
instance bound to the application the endpoint, role-id, and secret-id can be
parsed from the VCAP_SERVICES configuration by using the `--vcap` flag.  The
vcap flag expects a value of either org, space or service.  These values relate
to the broker generated Vault paths created by the HSDP Vault service and will
cause CCR to read that part of the path from the environment.  You will still
need to provide a `--path` value that will be appended to the base path
derived from VCAP_SERVICES.  Note this is specific to the HSDP Vault service
broker and not the open source HashiCorp Vault Service Broker.

**Example entrypoint script using VCAP bindings:**
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

Using CCR with environment variables
====================================
The most simple way to use CCR is with environment variables.  The environment
variables will be read and used to render configuration templates.  This mode
is useful for development or simple cases where there is only a couple of
variables.

When environment variables are used templates are inspected to discover the
variables that they require and only matching environment variables are pulled
into the rendering process.  This helps prevent pulling in extra or potentially
dangerous variables.

**Example entrypoint script using environment variables:**
```
#!/bin/sh
set -e

/ccr/ccr --from-env \
    -t /templates/my_config1.j2:/application/config/my_config1.conf \
    -t /templates/my_config2.j2:/application/config/my_config2.conf

exec /application/app_bin -c /application/config/my_config1.conf
```

Using CCR with Vault and environment variables
=======================
CCR can use merge variables from Vault and environment together by using the
`--merge-with-env` flag.  When merging variables environment variables will
always take precedence over Vault variables.  This also enables an easy way
to override a couple of variables from a much larger set of defaults that are
stored in Vault.

**Example entrypoint using both Vault and environment variables:**
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

Using CCR to create an environment file
====================
For applications that expect configuration to be sourced from environment
variables CCR can create an environment file from data stored in Vault.  The
resulting file needs to be sourced in the entrypoint script before launching
the final process.  The file will be written to `/dev/shm/environment`.  This
path should always exist in a docker container, but can be changed by providing
an alternate location with the `--out-file` option.

**Example entrypoint using vault and environment file:**
```
#!/bin/sh
set -e

/ccr/ccr --vcap service --path $vault_path --vault-to-env

source /dev/shm/environment

exec /application/app_bin
```
