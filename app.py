# Description: This file contains the main code for the Teamed backend. It is responsible for handling the database and the API endpoints.
import os
from flask import Flask, request, jsonify, render_template
import enum
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_restful import Api, Resource, reqparse
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS, cross_origin
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
import sqlite3

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
cors = CORS(app)
db = SQLAlchemy()
bcrypt = Bcrypt(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.db")
app.config['CORS_HEADERS'] = 'Content-Type'

##Swagger configuration

SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

app.register_blueprint(swaggerui_blueprint)

## End swagger configuration

db.init_app(app)

#type for distinguishing type of user in Teamed
user_type = {
    'FREELANCER': 'freelancer',
    'CLIENT': 'client',
    'PROJECT_MANAGER': 'project_manager'
}
#Different uesrs in Teamed
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, unique = True, nullable = False, autoincrement = True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    userType = db.Column(db.String(100), nullable=False)

    def __init__(self, name, email, password, userType):
        self.name = name
        self.email = email
        self.password = password
        self.userType = userType

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"
    
#Defined work and outline of what's going to happen
class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True , unique = True, nullable = False, autoincrement = True)
    idea = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)

    def __init__(self, idea, description):
        self.idea = idea
        self.description = description

    def __repr__(self):
        return f"Project('{self.idea}', '{self.description}')"
    
#Before something becomes a project, not worked on, approximated
class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.Integer, primary_key=True , unique = True, nullable = False, autoincrement = True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(50), nullable=False) #This needs to be a short summary of the project i.e Solar Power Manufacturer
    upper_estimate = db.Column(db.Integer, nullable=False) #This is the upper estimate of the project i.e 100000
    lower_estimate =  db.Column(db.Integer, nullable=False) #This is the lower estimate of the project i.e 50000
    closing_date = db.Column(db.String(100), nullable=False) #This is the closing date of the project i.e 2021-12-12
    status = db.Column(db.String(100), nullable=False) #This is the status of the project i.e prospect, submitted, successful, unsuccessful 

    def __init__(self, name, description, upper_estimate, lower_estimate, closing_date, status):
        self.name = name
        self.description = description
        self.upper_estimate = upper_estimate
        self.lower_estimate = lower_estimate
        self.closing_date = closing_date
        self.status = status

    def __repr__(self):
        return f"Lead('{self.name}', '{self.description}', '{self.upper_estimate}', '{self.lower_estimate}', '{self.closing_date}', '{self.status}')"
    
# Create all tables in the database
with app.app_context():
    db.create_all()

# helper functions

def validate_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return False
    return True

def get_user_data(user):
    users = User.query.all()
    user_data = {}
    for user in users:
        user_data['id'] = user.id
        user_data['name'] = user.name
        user_data['email'] = user.email
        user_data['userType'] = user.userType
    return user_data

@app.route('/')
def hello_world():
    return 'Welcome to Teamed backend'
'''
User Routes
'''
@app.route('/register', methods=['POST'])
@cross_origin()
def register():
        data = request.get_json()
        name = data['name']
        email = data['email']
        password = data['password']
        userType = data['userType']
        #validate user
        if (validate_user(email) == False):
            return jsonify({'message': 'User already exists'})
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(name, email, hashed, userType)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']
    user = User.query.filter_by(email=email).first()
    if user:
        if bcrypt.check_password_hash(user.password, password):
            user_data = get_user_data(user)
            login_response = jsonify({'message': 'Login successful', 'user': user_data})
            return login_response
    return jsonify({'message': 'Invalid credentials'})

#route to retrieve all data about a given user
@app.route('/users/<email>', methods=['GET'])
def get_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        user_data = {}
        user_data['id'] = user.id
        user_data['name'] = user.name
        user_data['email'] = user.email
        user_data['password'] = user.password
        user_data['userType'] = user.userType
        return jsonify({'user': user_data})
    else:
        return jsonify({'message': 'No user found'})

#test route 
@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    output = []
    for user in users:
        user_data = {}
        user_data['id'] = user.id
        user_data['name'] = user.name
        user_data['email'] = user.email
        user_data['password'] = user.password
        user_data['userType'] = user.userType
        output.append(user_data)
    return jsonify({'users': output})

'''
Lead Routes
'''
@app.route('/add_lead', methods=['POST'])
@cross_origin()
def add_lead():
    data = request.get_json()
    name = data['name']
    description = data['description']
    upper_estimate = data['upper_estimate']
    lower_estimate = data['lower_estimate']
    closing_date = data['closing_date']
    status = data['status']
    lead = Lead(name, description, upper_estimate, lower_estimate, closing_date, status)
    db.session.add(lead)
    db.session.commit()
    return jsonify({'message': 'Lead added successfully'})

@app.route('/leads', methods=['GET'])
def get_all_leads():
    leads = Lead.query.all()
    output = []
    for lead in leads:
        lead_data = {}
        lead_data['id'] = lead.id
        lead_data['name'] = lead.name
        lead_data['description'] = lead.description
        lead_data['upper_estimate'] = lead.upper_estimate
        lead_data['lower_estimate'] = lead.lower_estimate
        lead_data['closing_date'] = lead.closing_date
        lead_data['status'] = lead.status
        output.append(lead_data)
    return jsonify({'leads': output})
