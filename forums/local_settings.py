db = {
    'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    'NAME': 'forum.db',                      # Or path to database file if using sqlite3.
    # The following settings are not used with sqlite3:
    'USER': '',
    'PASSWORD': '',
    'HOST': '',  # Empty for localhost through domain sockets.
    'PORT': '',  # Set to empty string for default.
}
DATABASES = {
    'default': db,
    'spoken': db,
    'cdeep': db,
}
