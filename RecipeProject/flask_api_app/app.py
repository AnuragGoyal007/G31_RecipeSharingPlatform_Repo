from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, FileField
from wtforms.validators import DataRequired
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8000"],  # Your Django server
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

mail = Mail(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
jwt = JWTManager(app)

# Initialize Flask-RESTful
api = Api(app)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'users_customuser'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='commenter', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Recipe(db.Model):
    __tablename__ = 'recipe_app_recipe'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    cooking_method = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=True)
    calorie_count = db.Column(db.Integer, nullable=False)
    cooking_time = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(10), nullable=False, default='veg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users_customuser.id'), nullable=False)

    comments = db.relationship('Comment', backref='recipe_commented', lazy=True)

class Comment(db.Model):
    __tablename__ = 'recipe_app_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users_customuser.id'), nullable=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe_app_recipe.id'), nullable=False)

class ContactMessage(db.Model):
    __tablename__ = 'recipe_app_contactmessage'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# API Resources
class UserResource(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }

class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return [{
            'id': user.id,
            'username': user.username,
            'email': user.email
        } for user in users]

    def post(self):
        data = request.get_json()
        
        if not data or 'username' not in data or 'email' not in data or 'password' not in data:
            return {'error': 'Missing required fields'}, 400
            
        if User.query.filter_by(username=data['username']).first():
            return {'error': 'Username already exists'}, 400
            
        if User.query.filter_by(email=data['email']).first():
            return {'error': 'Email already exists'}, 400
            
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }, 201

class RecipeResource(Resource):
    def get(self, recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        return {
            'id': recipe.id,
            'title': recipe.title,
            'description': recipe.description,
            'ingredients': recipe.ingredients,
            'cooking_method': recipe.cooking_method,
            'calorie_count': recipe.calorie_count,
            'cooking_time': recipe.cooking_time,
            'category': recipe.category,
            'user_id': recipe.user_id
        }

    @jwt_required()
    def delete(self, recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        
        if recipe.image:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], recipe.image))
            except:
                pass
        
        db.session.delete(recipe)
        db.session.commit()
        return {'message': 'Recipe deleted successfully'}

class RecipeListResource(Resource):
    def get(self):
        recipes = Recipe.query.all()
        return [{
            'id': recipe.id,
            'title': recipe.title,
            'description': recipe.description,
            'ingredients': recipe.ingredients,
            'cooking_method': recipe.cooking_method,
            'calorie_count': recipe.calorie_count,
            'cooking_time': recipe.cooking_time,
            'category': recipe.category,
            'user_id': recipe.user_id,
            'created_at': recipe.created_at.isoformat() if recipe.created_at else None
        } for recipe in recipes]

    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['title', 'description', 'ingredients', 'cooking_method', 
                        'calorie_count', 'cooking_time', 'category']
        if not data or not all(field in data for field in required_fields):
            return {'error': 'Missing required fields'}, 400
            
        try:
            recipe = Recipe(
                title=data['title'],
                description=data['description'],
                ingredients=data['ingredients'],
                cooking_method=data['cooking_method'],
                calorie_count=int(data['calorie_count']),
                cooking_time=int(data['cooking_time']),
                category=data['category'],
                user_id=current_user_id
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            return {
                'id': recipe.id,
                'title': recipe.title,
                'message': 'Recipe created successfully'
            }, 201
            
        except ValueError as e:
            return {'error': 'Invalid data types'}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return {'error': 'Username and password are required'}, 400

        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return {'error': 'Invalid username or password'}, 401
        
        access_token = create_access_token(identity=user.id)
        
        return {
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, 200

# Register API resources
api.add_resource(UserListResource, '/api/users')
api.add_resource(UserResource, '/api/users/<int:user_id>')
api.add_resource(RecipeListResource, '/api/recipes')
api.add_resource(RecipeResource, '/api/recipes/<int:recipe_id>')
api.add_resource(LoginResource, '/api/login')

# Create test data
def create_test_data():
    """Create test data if none exists"""
    if not User.query.first():
        test_user = User(
            username='testuser',
            email='test@example.com'
        )
        test_user.set_password('testpass')
        db.session.add(test_user)
        db.session.commit()
        
        if not Recipe.query.first():
            test_recipe = Recipe(
                title='Test Recipe',
                description='This is a test recipe',
                ingredients='Ingredient 1, Ingredient 2',
                cooking_method='Step 1, Step 2',
                calorie_count=500,
                cooking_time=30,
                category='veg',
                user_id=test_user.id
            )
            db.session.add(test_recipe)
            db.session.commit()

# Initialize database and create test data
with app.app_context():
    db.create_all()
    create_test_data()

if __name__ == '__main__':
    app.run(debug=True)