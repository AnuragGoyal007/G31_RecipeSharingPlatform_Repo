import requests
from django.conf import settings
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)

class FlaskAPIError(Exception):
    """Custom exception for API errors"""
    pass

class FlaskAPIClient:
    def __init__(self, request=None):
        self.base_url = getattr(settings, 'FLASK_API_URL', 'http://localhost:5000')
        self.token = request.session.get('flask_token') if request else None
        self.session = requests.Session()
    
    def _make_request(self, method, endpoint, data=None, params=None, requires_auth=False):
        """Helper method to make API requests"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if requires_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            )
            
            # Log the request for debugging
            logger.debug(f"API Request: {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                error_msg = response.json().get('error', 'Unknown error occurred')
                logger.error(f"API Error: {error_msg}")
                raise FlaskAPIError(error_msg)
                
            return response.json()
            
        except RequestException as e:
            logger.error(f"API Connection Error: {str(e)}")
            raise FlaskAPIError(f"Could not connect to API: {str(e)}")

    # Authentication Endpoints
    def login(self, username, password):
        """Authenticate with the Flask API"""
        endpoint = '/api/login'
        data = {
            'username': username,
            'password': password
        }
        try:
            result = self._make_request('POST', endpoint, data=data)
            self.token = result.get('access_token')
            return result
        except FlaskAPIError as e:
            logger.error(f"Login failed: {str(e)}")
            return None
    
    # User Endpoints
    def get_users(self):
        """Get all users"""
        return self._make_request('GET', '/api/users', requires_auth=True)
    
    def get_user(self, user_id):
        """Get a specific user"""
        return self._make_request('GET', f'/api/users/{user_id}', requires_auth=True)
    
    def create_user(self, user_data):
        """Create a new user"""
        required_fields = ['username', 'email', 'password']
        if not all(field in user_data for field in required_fields):
            raise ValueError("Missing required user fields")
        
        return self._make_request('POST', '/api/users', data=user_data)
    
    def delete_user(self, user_id):
        """Delete a user"""
        return self._make_request('DELETE', f'/api/users/{user_id}', requires_auth=True)
    
    # Recipe Endpoints
    def get_recipes(self, category=None):
        """Get all recipes, optionally filtered by category"""
        params = {}
        if category in ['veg', 'nonveg']:
            params['category'] = category
            
        return self._make_request('GET', '/api/recipes', params=params)
    
    def get_recipe(self, recipe_id):
        """Get a specific recipe"""
        return self._make_request('GET', f'/api/recipes/{recipe_id}')
    
    def create_recipe(self, recipe_data):
        """Create a new recipe"""
        required_fields = [
        'title', 'description', 'ingredients', 'cooking_method',
        'calorie_count', 'cooking_time', 'category', 'user_id'
    ]
        if not all(field in recipe_data for field in required_fields):
            missing = [field for field in required_fields if field not in recipe_data]
            raise ValueError(f"Missing required recipe fields: {missing}")
    
        print("Sending to API:", recipe_data)  # Debug print
        print("API URL:", f"{self.base_url}/api/recipes")  # Debug print
    
        try:
            response = self._make_request('POST', '/api/recipes', data=recipe_data, requires_auth=True)
            print("API Response:", response)  # Debug print
            return response
        except Exception as e:
            print("API Request Failed:", str(e))  # Debug print
        raise
    
    def update_recipe(self, recipe_id, recipe_data):
        """Update an existing recipe"""
        return self._make_request('PUT', f'/api/recipes/{recipe_id}', data=recipe_data, requires_auth=True)
    
    def delete_recipe(self, recipe_id):
        """Delete a recipe"""
        return self._make_request('DELETE', f'/api/recipes/{recipe_id}', requires_auth=True)
    
    # Comment Endpoints (if you add them to your API)
    def get_comments(self, recipe_id):
        """Get comments for a recipe"""
        return self._make_request('GET', f'/api/recipes/{recipe_id}/comments')
    
    def create_comment(self, recipe_id, content, user_id):
        """Create a new comment"""
        data = {
            'content': content,
            'user_id': user_id,
            'recipe_id': recipe_id
        }
        return self._make_request('POST', f'/api/recipes/{recipe_id}/comments', data=data, requires_auth=True)
    
    # Contact Endpoints
    def get_contact_messages(self):
        """Get all contact messages (admin only)"""
        return self._make_request('GET', '/api/contact', requires_auth=True)
    
    def get_contact_message(self, message_id):
        """Get a specific contact message (admin only)"""
        return self._make_request('GET', f'/api/contact/{message_id}', requires_auth=True)
    
    def create_contact_message(self, name, email, message):
        """Create a new contact message"""
        data = {
            'name': name,
            'email': email,
            'message': message
        }
        return self._make_request('POST', '/api/contact', data=data)
    
    def mark_message_read(self, message_id):
        """Mark a message as read (admin only)"""
        return self._make_request('POST', f'/api/contact/{message_id}/mark-read', requires_auth=True)