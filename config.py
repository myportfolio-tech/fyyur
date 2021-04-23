import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True

# Connect to the database

user = 'psqladmin'
pwd = 'administrator'
server = 'localhost'
database = 'fyyur' 
port = 5432


SQLALCHEMY_DATABASE_URI = f'postgresql://{user}:{pwd}@{server}:{port}/{database}'
SQLALCHEMY_TRACK_MODIFICATIONS = False



