import os

class Config(object):
    CREDENTIAL_FILE = 'secret.json'
    MYSQL_HOST = 'mysql'
    MYSQL_USER = os.environ["DB-USER"]
    MYSQL_PASSWORD = os.environ["DB-PASSWORD"]
    MYSQL_DB = os.environ["DB-NAME"]
    LOG_LEVEL = 'INFO'

class DebugConfig(Config):
    LOG_LEVEL = 'DEBUG'