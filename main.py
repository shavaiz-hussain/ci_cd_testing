import os

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)
from flask_login import (LoginManager, UserMixin, login_required, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

db = SQLAlchemy()  # Initialize SQLAlchemy globally
login_manager = LoginManager()  # Initialize Flask-Login globally

# --- Models ---

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Admin user type

    # One-to-One relationship with Profile
    profile = db.relationship('Profile', backref='user', uselist=False)

# Profile model (related to User)
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign Key to User

# --- App Factory Function ---

def create_app(config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret!'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'  # Database configuration
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    if config:
        app.config.update(config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Routes ---
    @app.route('/')
    @login_required
    def chat():
        return render_template('chat.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            # Validate user credentials
            user = User.query.filter_by(username=username, password=password).first()
            if user:
                login_user(user)
                return redirect(url_for('chat'))
            else:
                flash('Invalid credentials')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/upload_file', methods=['POST'])
    def file_upload():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400

        file = request.files['file']
        if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return jsonify({'message': f'File {filename} uploaded successfully'}), 201

        return jsonify({'error': 'Invalid file type'}), 400

    # --- Helper Functions ---
    def allowed_file(filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    @app.route('/users', methods=['POST'])
    def create_user():
        """Create a new user with an optional profile."""
        data = request.json
        username = data.get('username')
        password = data.get('password')
        full_name = data.get('full_name')
        bio = data.get('bio')

        # Check if username is unique
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400

        # Create user
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        # Create profile if provided
        if full_name:
            profile = Profile(full_name=full_name, bio=bio, user_id=user.id)
            db.session.add(profile)
            db.session.commit()

        return jsonify({'message': f'User {username} created successfully'}), 201

    @app.route('/users/<int:user_id>', methods=['GET'])
    @login_required
    def get_user(user_id):
        """Retrieve a user by ID, including their profile if available."""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_data = {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'profile': {
                'full_name': user.profile.full_name if user.profile else None,
                'bio': user.profile.bio if user.profile else None
            } if user.profile else None
        }
        return jsonify(user_data)

    @app.route('/users/<int:user_id>', methods=['PUT'])
    def update_user(user_id):
        """Update user details and their associated profile."""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.json
        user.username = data.get('username', user.username)
        user.password = data.get('password', user.password)

        if user.profile:
            user.profile.full_name = data.get('full_name', user.profile.full_name)
            user.profile.bio = data.get('bio', user.profile.bio)
        else:
            if 'full_name' in data:
                profile = Profile(
                    full_name=data['full_name'],
                    bio=data.get('bio'),
                    user_id=user.id
                )
                db.session.add(profile)

        db.session.commit()
        return jsonify({'message': f'User {user.username} updated successfully'})

    @app.route('/users/<int:user_id>', methods=['DELETE'])
    def delete_user(user_id):
        """Delete a user and their associated profile."""
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Delete profile first
        if user.profile:
            db.session.delete(user.profile)

        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': f'User {user.username} deleted successfully'})

    @app.route('/profiles/<int:user_id>', methods=['GET'])
    def get_profile(user_id):
        """Retrieve a user's profile by their user ID."""
        user = User.query.get(user_id)
        if not user or not user.profile:
            return jsonify({'error': 'Profile not found'}), 404

        profile_data = {
            'full_name': user.profile.full_name,
            'bio': user.profile.bio
        }
        return jsonify(profile_data)
    return app


# --- Database Initialization ---
def setup_database(app):
    """Ensure tables are created."""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app = create_app()
    setup_database(app)
    app.run(debug=True)
