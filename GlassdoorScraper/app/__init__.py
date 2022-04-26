from flask import Flask, g
from flask_mysqldb import MySQL
from app.controllers import controller
import os
import logging

def setConfigInfo():

    if os.environ['API-MODE'] == 'development':
        flaskapp.config.from_object('config.DebugConfig')
    else:
        flaskapp.config.from_object('config.Config')

    flaskapp.logger.setLevel(flaskapp.config['LOG_LEVEL'])



# Instantiating our app
flaskapp = Flask(__name__)
setConfigInfo()

db = MySQL()
db.init_app(flaskapp)

@flaskapp.before_request
def before_request():

    # Instantiating our database connection and cursor
    g.dbcon = db
    g.dbcursor = db.connection.cursor()
    g.credentialFile = flaskapp.config.get('CREDENTIAL_FILE')
    g.appLogger = flaskapp.logger

# Registering our controllers Blueprint
flaskapp.register_blueprint(controller)