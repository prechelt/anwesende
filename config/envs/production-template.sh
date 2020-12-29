# to be bash-sourced

# source .envs/otherenv.sh   # uncomment and modify to derive from some base config

# Overall configuration
# ---------------------
# One of the following values (case-sensitive):
# LETSENCRYPT: use traefik webserver with Let's Encrypt for https
# CERTS:       use traefik webserver with manually created certificates
# GUNICORN:    expose the Gunicorn app server (for use behind existing web server)
DEPLOYMODE=CERTS
# 0 if build and execution are to happen on the _same_ server, 1 otherwise:
REMOTE=1
# shorter name for 'production', used for image names and path names:
ENV_SHORTNAME=prod

# Settings required for DEPLOYMODE=LETSENCRYPT only
# -------------------------------------------------
# Name by which the web server will be known to its users:
SERVERNAME=anwesende.example.com
# Email address how let's encrypt can reach the server admin:
LETSENCRYPTEMAIL=anwesende-admin@myuniversity.de

# Relationship between source machine and server
# ----------------------------------------------
# This whole block applies to REMOTE=1 only and values should be empty otherwise.
# Target user at target host: an ssh-style user@machine:port string
# needed to copy a few files and for remote script execution
TUTH=prechelt@anwesende.imp.fu-berlin.de
# Docker registry name and user (for login) and prefix string (for tag names).
# Docker images are built locally then transfered to server via the registry.
REGISTRY=git.imp.fu-berlin.de:5000
REGISTRYUSER=prechelt
REGISTRYPREFIX=git.imp.fu-berlin.de:5000/anwesende/anwesende

# Port numbers
# ------------
# Required for deploymode GUNICORN only: what port to expose it on
GUNICORN_PORT=5005
# Required for deploymodes LETSENCRYPT and CERTS only:
TRAEFIK_HTTP_PORT=80
TRAEFIK_HTTPS_PORT=443

# Django container
# ------------------------------------------------------------------------------
# Which user ID and group ID the Django process should have,
# e.g. those of the installing user's login (obtain them by command 'id')
DJANGO_UID=118205
DJANGO_GID=10005

# Docker environment modifications
# --------------------------------
# Variables called PATCH_XYZ will overwrite variable XYZ defined in the
# global docker environment file derived from myenv.env when myenv.env
# is processed into autogenerated.env.
# Multiword values must be quoted here and will arrive there without quotes.
PATCH_DJANGO_HTTPS_INSIST=False


# Docker volumes
# ------------------------------------------------------------------------------
# Which directories on the server the docker containers created by
# the docker-compose file will use to store their data.
: ${VOLUMEDIR_PREFIX:=/srv/anwesende/$ENV_SHORTNAME}
# Django logging files directory:
VOLUME_SERVERDIR_DJANGO_LOG=$VOLUMEDIR_PREFIX/djangolog
# The database as such:
VOLUME_SERVERDIR_POSTGRES_DATA=$VOLUMEDIR_PREFIX/postgres_data
# Plain-SQL backups of the database:
VOLUME_SERVERDIR_POSTGRES_BACKUP=$VOLUMEDIR_PREFIX/postgres_backup
# Certificate/key store (for DEPLOYMODE=LETSENCRYPT only):
VOLUME_SERVERDIR_TRAEFIK_ACME=$VOLUMEDIR_PREFIX/traefik_acme
# Certificate/key store (for DEPLOYMODE=CERTS only):
VOLUME_SERVERDIR_TRAEFIK_SSL=$VOLUMEDIR_PREFIX/traefik_ssl
