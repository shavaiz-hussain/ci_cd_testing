import pytest
from sqlalchemy.exc import IntegrityError

from main import Profile, User, create_app, db


@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_session(app):
    """Provide a session-wide database fixture."""
    with app.app_context():
        yield db
        db.session.rollback()



def test_create_user(client, db_session):
    """Test creating a new user."""
    # Create a new user
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    # Check that the user was created
    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.username == 'testuser'
    assert user.password == 'testpassword'
    assert user.is_admin is False


def test_create_user_with_existing_username(client, db_session):
    """Test creating a user with an existing username."""
    # Create a new user
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    # Try to create another user with the same username
    new_user2 = User(username='testuser', password='testpassword2', is_admin=False)
    db_session.session.add(new_user2)
    with pytest.raises(IntegrityError):
        db_session.session.commit()


def test_update_user(client, db_session):
    """Test updating an existing user's information."""
    # Create a new user
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    # Update the user
    user = User.query.filter_by(username='testuser').first()
    user.username = 'newusername'
    user.password = 'newpassword'
    user.is_admin = True
    db_session.session.commit()

    # Check that the user was updated
    user = User.query.filter_by(username='newusername').first()
    assert user is not None
    assert user.username == 'newusername'
    assert user.password == 'newpassword'
    assert user.is_admin is True


def test_update_user_with_existing_username(client, db_session):
    """Test updating a user to an existing username."""
    # Create two new users
    new_user1 = User(username='testuser1', password='testpassword1', is_admin=False)
    new_user2 = User(username='testuser2', password='testpassword2', is_admin=False)
    db_session.session.add_all([new_user1, new_user2])
    db_session.session.commit()

    # Update the first user with the second user's username
    user1 = User.query.filter_by(username='testuser1').first()
    user1.username = 'testuser2'
    with pytest.raises(IntegrityError):
        db_session.session.commit()



def test_delete_user(client, db_session):
    """Test deleting a user."""
    # Create a new user
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    # Delete the user
    user = User.query.filter_by(username='testuser').first()
    db_session.session.delete(user)
    db_session.session.commit()

    # Check that the user was deleted
    user = User.query.filter_by(username='testuser').first()
    assert user is None


def test_create_profile(client, db_session):
    """Test creating a profile for a user."""
    # Create a new user
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    # Create a new profile for the user
    new_profile = Profile(full_name='Test User', bio='This is a test profile', user_id=new_user.id)
    db_session.session.add(new_profile)
    db_session.session.commit()

    # Check that the profile was created
    profile = Profile.query.filter_by(user_id=new_user.id).first()
    assert profile is not None
    assert profile.full_name == 'Test User'
    assert profile.bio == 'This is a test profile'



def test_update_profile(client, db_session):
    """Test updating a user's profile."""
    # Create a new user and profile
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    new_profile = Profile(full_name='Test User', bio='This is a test profile', user_id=new_user.id)
    db_session.session.add(new_profile)
    db_session.session.commit()

    # Update the profile
    profile = Profile.query.filter_by(user_id=new_user.id).first()
    profile.full_name = 'New Test User'
    profile.bio = 'This is a new test profile'
    db_session.session.commit()

    # Check that the profile was updated
    profile = Profile.query.filter_by(user_id=new_user.id).first()
    assert profile is not None
    assert profile.full_name == 'New Test User'
    assert profile.bio == 'This is a new test profile'



def test_delete_profile(client, db_session):
    """Test deleting a user's profile."""
    # Create a new user and profile
    new_user = User(username='testuser', password='testpassword', is_admin=False)
    db_session.session.add(new_user)
    db_session.session.commit()

    new_profile = Profile(full_name='Test User', bio='This is a test profile', user_id=new_user.id)
    db_session.session.add(new_profile)
    db_session.session.commit()

    # Delete the profile
    profile = Profile.query.filter_by(user_id=new_user.id).first()
    db_session.session.delete(profile)
    db_session.session.commit()

    # Check that the profile was deleted
    profile = Profile.query.filter_by(user_id=new_user.id).first()
    assert profile is None
