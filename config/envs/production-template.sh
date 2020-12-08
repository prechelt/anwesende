# Port numbers
# ------------
# Required for deploymode GUNICORN only: what port to expose it on
GUNICORN_PORT=5005

# docker volumes
# ------------------------------------------------------------------------------
# Which directories on the server the docker containers created by
# the docker-compose file will use to store their data.
# You can change these paths as needed. 
ANW_HOSTDIR_DJANGO_LOG=/srv/anwesende/p/django_log
# The database as such:
ANW_HOSTDIR_POSTGRES_DATA=/srv/anwesende/p/postgres_data
# Plain-SQL backups of the database:
ANW_HOSTDIR_POSTGRES_BACKUP=/srv/anwesende/p/postgres_backup
# Certificate/key store if Traefik uses LetsEncrypt:
ANW_HOSTDIR_TRAEFIK_ACME=/srv/anwesende/p/traefik_acme
# Certificate/key store if Traefik uses manually created certificates:
ANW_HOSTDIR_TRAEFIK_SSL=/srv/anwesende/p/traefik_ssl
