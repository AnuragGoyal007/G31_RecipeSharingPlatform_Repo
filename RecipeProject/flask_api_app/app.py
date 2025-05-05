from flask import Flask, render_template, request, redirect, url_for, flash
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
from flask_restful import Resource,Api
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import check_password_hash

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

mail = Mail(app)
db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#--------------------------------------------------------------------------------------------------

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
jwt = JWTManager(app)

api = Api(app)

from flask_restful import Resource, Api

# Initialize Flask-RESTful
api = Api(app)



from flask_cors import CORS

# Allow requests from your Django domain
CORS(app, resources={
    r"/api/login": {
        "origins": ["http://your-django-domain.com"],
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable for API endpoints

class UserResource(Resource):
    def get(self, user_id):
        user = User.query.get_or_404(user_id)
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }

    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {'message': 'User deleted successfully'}

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
        
        # Simple validation
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

    def delete(self, recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Delete associated image if exists
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
            'user_id': recipe.user_id
        } for recipe in recipes]

    def post(self):
        data = request.get_json()
        
        # Basic validation
        required_fields = ['title', 'description', 'ingredients', 'cooking_method', 
                        'calorie_count', 'cooking_time', 'category', 'user_id']
        if not data or not all(field in data for field in required_fields):
            return {'error': 'Missing required fields'}, 400
            
        recipe = Recipe(
            title=data['title'],
            description=data['description'],
            ingredients=data['ingredients'],
            cooking_method=data['cooking_method'],
            calorie_count=data['calorie_count'],
            cooking_time=data['cooking_time'],
            category=data['category'],
            user_id=data['user_id']
        )
        
        db.session.add(recipe)
        db.session.commit()
        
        return {
            'id': recipe.id,
            'title': recipe.title,
            'message': 'Recipe created successfully'
        }, 201

class LoginResource(Resource):
    def post(self):
        data = request.get_json()
        
        # Basic validation
        if not data or 'username' not in data or 'password' not in data:
            return {'error': 'Username and password are required'}, 400

        user = User.query.filter_by(username=data['username']).first()
        
        # Verify user exists and password is correct
        if not user or not check_password_hash(user.password_hash, data['password']):
            return {'error': 'Invalid username or password'}, 401
        
        # Create access token
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
    
# Contact Resources
class ContactResource(Resource):
    @jwt_required()
    def get(self, message_id):
        if not current_user.is_admin:
            return make_response({'error': 'Unauthorized'}, 403)
        
        message = ContactMessage.query.get_or_404(message_id)
        return make_response({
            'id': message.id,
            'name': message.name,
            'email': message.email,
            'message': message.message
        })

class ContactListResource(Resource):
    def post(self):
        data = request.get_json()
        if not data or not all(key in data for key in ['name', 'email', 'message']):
            return make_response({'error': 'Missing required fields'}, 400)
        
        contact = ContactMessage(
            name=data['name'],
            email=data['email'],
            message=data['message']
        )
        db.session.add(contact)
        db.session.commit()


# Register the resources
api.add_resource(UserListResource, '/api/users') # To create a new user
api.add_resource(LoginResource, '/api/login') # To login
api.add_resource(UserResource, '/api/users/<int:user_id>') # To get a particular user's details
api.add_resource(RecipeListResource, '/api/recipes') # To get all recipes
api.add_resource(RecipeResource, '/api/recipes/<int:recipe_id>') # To get recipe by its ID
api.add_resource(ContactListResource, '/api/contact')
api.add_resource(ContactResource, '/api/contact/<int:message_id>')







#-------------------------------------------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users_customuser'
    
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(128))
    last_login = db.Column(db.DateTime, nullable=True)
    is_superuser = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    first_name = db.Column(db.String(150), default='')
    last_name = db.Column(db.String(150), default='')
    email = db.Column(db.String(254), unique=True, nullable=False)
    is_staff = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Additional custom fields
    profile_picture = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    website = db.Column(db.String(200), nullable=True)
    user_type = db.Column(db.String(10), default='user')
    
    # Explicitly specify which foreign key to use in relationships
    recipes = db.relationship('Recipe', 
                            backref='author', 
                            lazy=True,
                            foreign_keys='Recipe.user_id')  # Specify which FK to use
    
    comments = db.relationship('Comment', 
                            backref='commenter', 
                            lazy=True,
                            foreign_keys='Comment.user_id')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
        
    def is_admin(self):
        return self.is_superuser

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
    allergic_content = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(10), nullable=False, default='veg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ForeignKeys - specify which one is for the relationship
    user_id = db.Column(db.Integer, db.ForeignKey('users_customuser.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users_customuser.id'), nullable=False)
    
    # Relationships with explicit foreign_keys
    comments = db.relationship('Comment', 
                            backref='recipe_commented', 
                            lazy=True,
                            foreign_keys='Comment.recipe_id')

    def get_ingredients_list(self):
        return [ingredient.strip() for ingredient in self.ingredients.split(",")] if self.ingredients else []

    def get_cooking_method_list(self):
        return [step.strip() for step in self.cooking_method.split(",")] if self.cooking_method else []


class ContactMessage(db.Model):
    __tablename__ = 'recipe_app_contactmessage'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    cooking_method = TextAreaField('Cooking Method', validators=[DataRequired()])
    image = FileField('Recipe Image')
    calorie_count = IntegerField('Calories', validators=[DataRequired()])
    cooking_time = IntegerField('Cooking Time (minutes)', validators=[DataRequired()])
    allergic_content = StringField('Allergens (optional)')
    category = SelectField('Category', choices=[('veg', 'Vegetarian'), ('nonveg', 'Non-Vegetarian')], validators=[DataRequired()])

class Comment(db.Model):
    __tablename__ = 'recipe_app_comment'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ForeignKeys
    user_id = db.Column(db.Integer, db.ForeignKey('users_customuser.id'), nullable=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe_app_recipe.id'), nullable=False)
    

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    content = request.form.get('content')
    
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        recipe_id=recipe_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding comment. Please try again.', 'error')
        app.logger.error(f'Error adding comment: {str(e)}')
    
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/recipe/<int:recipe_id>/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(recipe_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        flash('You are not authorized to edit this comment.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash('Comment cannot be empty.', 'error')
            return redirect(url_for('edit_comment', recipe_id=recipe_id, comment_id=comment_id))
        
        comment.content = content
        try:
            db.session.commit()
            flash('Comment updated successfully!', 'success')
            return redirect(url_for('recipe_detail', recipe_id=recipe_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating comment. Please try again.', 'error')
            app.logger.error(f'Error updating comment: {str(e)}')
    
    return render_template('edit_comment.html', comment=comment, recipe_id=recipe_id)

@app.route('/recipe/<int:recipe_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(recipe_id, comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        flash('You are not authorized to delete this comment.', 'error')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting comment. Please try again.', 'error')
        app.logger.error(f'Error deleting comment: {str(e)}')
    
    return redirect(url_for('recipe_detail', recipe_id=recipe_id)) 

@app.route('/')
def home():
    category = request.args.get('category')
    if category == 'veg':
        recipes = Recipe.query.filter_by(category='veg').order_by(Recipe.created_at.desc()).all()
    elif category == 'nonveg':
        recipes = Recipe.query.filter_by(category='nonveg').order_by(Recipe.created_at.desc()).all()
    else:
        recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return render_template('home.html', recipes=recipes)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    if form.validate_on_submit():
        try:
            # Handle image upload
            image_filename = None
            if form.image.data:
                image = form.image.data
                filename = secure_filename(image.filename)
                # Create a unique filename to prevent overwrites
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image.save(image_path)
                image_filename = unique_filename

            # Create new recipe
            recipe = Recipe(
                title=form.title.data,
                description=form.description.data,
                ingredients=form.ingredients.data,
                cooking_method=form.cooking_method.data,
                image=image_filename,
                calorie_count=form.calorie_count.data,
                cooking_time=form.cooking_time.data,
                allergic_content=form.allergic_content.data,
                category=form.category.data,
                user_id=current_user.id
            )

            db.session.add(recipe)
            db.session.commit()
            flash('Recipe created successfully!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating recipe: {str(e)}', 'error')
            app.logger.error(f'Error creating recipe: {str(e)}')
            return redirect(url_for('new_recipe'))

    return render_template('new_recipe.html', form=form)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    return render_template('recipe_detail.html', recipe=recipe)

@app.route('/contact', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Store message in database
        contact_message = ContactMessage(
            name=name,
            email=email,
            message=message
        )
        
        try:
            db.session.add(contact_message)
            db.session.commit()
            flash('Thank you for your message! We will get back to you soon.')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash('Sorry, there was an error sending your message. Please try again later.')
            app.logger.error(f'Error saving contact message: {str(e)}')
            return redirect(url_for('contact_us'))
    
    return render_template('contact.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's recipes
    user_recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    
    # Get recipe count
    recipe_count = len(user_recipes)
    
    # Get latest recipe
    latest_recipe = user_recipes[0] if user_recipes else None
    
    return render_template('dashboard.html', 
                    user_recipes=user_recipes,
                    recipe_count=recipe_count,
                    latest_recipe=latest_recipe)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if the current user is the author of the recipe
    if recipe.user_id != current_user.id:
        flash('You are not authorized to edit this recipe.', 'error')
        return redirect(url_for('dashboard'))
    
    form = RecipeForm(obj=recipe)
    if form.validate_on_submit():
        try:
            # Handle image upload
            if form.image.data:
                # Delete old image if exists
                if recipe.image:
                    old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Save new image
                image = form.image.data
                filename = secure_filename(image.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                image.save(image_path)
                recipe.image = unique_filename

            # Update recipe details
            recipe.title = form.title.data
            recipe.description = form.description.data
            recipe.ingredients = form.ingredients.data
            recipe.cooking_method = form.cooking_method.data
            recipe.calorie_count = form.calorie_count.data
            recipe.cooking_time = form.cooking_time.data
            recipe.allergic_content = form.allergic_content.data
            recipe.category = form.category.data

            db.session.commit()
            flash('Recipe updated successfully!', 'success')
            return redirect(url_for('recipe_detail', recipe_id=recipe.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating recipe: {str(e)}', 'error')
            app.logger.error(f'Error updating recipe: {str(e)}')
    
    return render_template('edit_recipe.html', form=form, recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    
    # Check if the current user is the author of the recipe
    if recipe.user_id != current_user.id:
        flash('You are not authorized to delete this recipe.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Delete image file if exists
            if recipe.image:
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], recipe.image)
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            db.session.delete(recipe)
            db.session.commit()
            flash('Recipe deleted successfully!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting recipe: {str(e)}', 'error')
            app.logger.error(f'Error deleting recipe: {str(e)}')
    
    return render_template('delete_recipe.html', recipe=recipe)

@app.route('/admin/contact-messages')
@login_required
def view_contact_messages():
    if not current_user.is_admin:
        flash('You are not authorized to view this page.', 'error')
        return redirect(url_for('home'))
    
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/contact_messages.html', messages=messages)

@app.route('/admin/contact-messages/<int:message_id>/mark-read')
@login_required
def mark_message_read(message_id):
    if not current_user.is_admin:
        flash('You are not authorized to perform this action.', 'error')
        return redirect(url_for('home'))
    
    message = ContactMessage.query.get_or_404(message_id)
    message.is_read = True
    db.session.commit()
    flash('Message marked as read.', 'success')
    return redirect(url_for('view_contact_messages'))



@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()
    app.run(debug=True) 