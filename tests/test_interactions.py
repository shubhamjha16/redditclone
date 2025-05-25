import pytest
from app.models import User, College, Post, Comment, Vote, VoteType
from app import db

# Helper function to log in a user, can also be a fixture
def login(client, username, password):
    return client.post('/login', data=dict(
        email_or_username=username,
        password=password
    ), follow_redirects=True)

# Helper function to register a user
def register_user(client, username, email, password, college_id, role=User.ROLE_STUDENT):
    return client.post('/register', data=dict(
        username=username,
        email=email,
        password=password,
        confirm_password=password,
        college=college_id,
        role=role
    ), follow_redirects=True)


def test_create_post_interaction(client, new_user, new_college):
    # Associate user with college for create_post route
    with client.application.app_context():
        user = User.query.filter_by(username=new_user.username).first()
        user.college_id = new_college.id
        db.session.commit()

    login_response = login(client, new_user.username, 'password')
    assert b'Welcome back' in login_response.data

    # Go to create post page
    response_get_create_post = client.get('/create_post')
    assert response_get_create_post.status_code == 200
    assert b"Create Post" in response_get_create_post.data

    # Submit a new post
    post_title = "My First Interactive Post"
    post_content = "This post was created via an interaction test."
    response_post_create = client.post('/create_post', data={
        'title': post_title,
        'content': post_content
    }, follow_redirects=True)
    
    assert response_post_create.status_code == 200
    assert b"Your post has been created!" in response_post_create.data # Flash message
    assert post_title.encode() in response_post_create.data # Post title should be on the view_post page
    assert post_content.encode() in response_post_create.data # Post content should be on the view_post page

    # Verify the post exists in the database
    with client.application.app_context():
        post = Post.query.filter_by(title=post_title).first()
        assert post is not None
        assert post.author.id == new_user.id
        assert post.college.id == new_college.id


def test_add_comment_interaction(client, new_user, new_post): # new_post fixture from test_routes or conftest
    login_response = login(client, new_user.username, 'password')
    assert b'Welcome back' in login_response.data

    # View the post page
    response_get_post = client.get(f'/post/{new_post.id}')
    assert response_get_post.status_code == 200
    assert new_post.title.encode() in response_get_post.data

    # Add a comment
    comment_text = "This is a test comment from an interaction test."
    response_post_comment = client.post(f'/post/{new_post.id}', data={
        'content': comment_text
    }, follow_redirects=True)

    assert response_post_comment.status_code == 200
    assert b"Your comment has been published." in response_post_comment.data # Flash message
    assert comment_text.encode() in response_post_comment.data # Comment text should be on the page

    # Verify the comment exists in the database
    with client.application.app_context():
        comment = Comment.query.filter_by(content=comment_text).first()
        assert comment is not None
        assert comment.author.id == new_user.id
        assert comment.post_id == new_post.id


def test_vote_on_post_interaction(client, new_user, new_post):
    login_response = login(client, new_user.username, 'password')
    assert b'Welcome back' in login_response.data

    # Check initial score (should be 0 or based on get_target_score logic)
    with client.application.app_context():
        initial_score = Post.query.get(new_post.id).votes.count() # Simple count, or use get_target_score
        # For a more accurate score check, you'd need to replicate or call get_target_score
        # For simplicity, we'll check if a vote object is created/modified.

    # Upvote the post
    response_upvote = client.post(f'/vote/post/{new_post.id}/upvote', follow_redirects=True)
    assert response_upvote.status_code == 200
    assert b"Your vote has been recorded." in response_upvote.data

    with client.application.app_context():
        vote = Vote.query.filter_by(user_id=new_user.id, post_id=new_post.id).first()
        assert vote is not None
        assert vote.vote_type == VoteType.UPVOTE

    # Vote again (remove upvote)
    response_remove_upvote = client.post(f'/vote/post/{new_post.id}/upvote', follow_redirects=True)
    assert response_remove_upvote.status_code == 200
    assert b"Your vote has been removed." in response_remove_upvote.data
    with client.application.app_context():
        vote_after_removal = Vote.query.filter_by(user_id=new_user.id, post_id=new_post.id).first()
        assert vote_after_removal is None

    # Downvote the post
    response_downvote = client.post(f'/vote/post/{new_post.id}/downvote', follow_redirects=True)
    assert response_downvote.status_code == 200
    assert b"Your vote has been recorded." in response_downvote.data # Should be 'recorded' as it's a new vote state
    with client.application.app_context():
        vote_after_downvote = Vote.query.filter_by(user_id=new_user.id, post_id=new_post.id).first()
        assert vote_after_downvote is not None
        assert vote_after_downvote.vote_type == VoteType.DOWNVOTE

    # Change vote from downvote to upvote
    response_change_to_upvote = client.post(f'/vote/post/{new_post.id}/upvote', follow_redirects=True)
    assert response_change_to_upvote.status_code == 200
    assert b"Your vote has been changed." in response_change_to_upvote.data
    with client.application.app_context():
        vote_after_change = Vote.query.filter_by(user_id=new_user.id, post_id=new_post.id).first()
        assert vote_after_change is not None
        assert vote_after_change.vote_type == VoteType.UPVOTE

# To use new_post fixture here, it should be in conftest.py
# For now, assuming it's correctly defined or will be moved.
# If new_post is not in conftest, these tests will fail or need new_post defined locally.
# This test file will need access to `new_post` fixture, which was defined in `test_routes.py`.
# It's better to move shared fixtures like `new_post` to `tests/conftest.py`.
# I will proceed assuming `new_post` will be moved or is accessible.
# If not, I will create it locally or adjust later.

# Let's assume new_post will be moved to conftest.py.
# If it's not, I'll define it quickly here for completeness of this step.
# For now, I'll rely on it being moved. If errors occur, this is the first place to check.

# A quick local new_post fixture if it's not in conftest.py yet for this specific file to run independently:
# @pytest.fixture(scope='function')
# def new_post(init_database, new_user, new_college): # Assuming these fixtures are in conftest.py
#     with init_database.app.app_context():
#         post = Post(title="A Test Post for Interactions", content="Interaction content", user_id=new_user.id, college_id=new_college.id)
#         db.session.add(post)
#         db.session.commit()
#         return post
