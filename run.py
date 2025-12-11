# import os
# from datetime import datetime
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# from werkzeug.utils import secure_filename
# # from flask_login import current_user, login_required
# from flask_socketio import SocketIO
# # from extensions import db
# from models import db, Post, User, Comment

# # Create Flask app
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'supersecretkey'
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize extensions
# db.init_app(app)
# socketio = SocketIO(app)

# # # Create DB tables
# with app.app_context():
#     db.create_all()

# # In-memory posts for demo (until DB is used)
# posts = []

# # Helper: human-readable time difference
# def time_since(post_time):
#     now = datetime.now()
#     diff = now - post_time
#     seconds = int(diff.total_seconds())
#     minutes = seconds // 60
#     hours = minutes // 60
#     days = diff.days

#     if seconds < 60:
#         return f"{seconds} second{'s' if seconds != 1 else ''} ago"
#     elif minutes < 60:
#         return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
#     elif hours < 24:
#         return f"{hours} hour{'s' if hours != 1 else ''} ago"
#     elif days < 7:
#         return f"{days} day{'s' if days != 1 else ''} ago"
#     else:
#         return post_time.strftime("%b %d")  # Example: "Sep 14"

# # Routes
# @app.route('/')
# def home():
#     return render_template("index.html", posts=posts)

# @app.route("/upload", methods=["GET", "POST"])
# def upload_post():
#     if request.method == "POST":
#         image = request.files['image']
#         caption = request.form["caption"]

#         if image:
#             filename = secure_filename(image.filename)
#             filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#             image.save(filepath)

#             post = {
#                 "id": len(posts),
#                 "username": "Jīvanapāṭhaḥ",
#                 "image": f"static/uploads/{filename}",
#                 "caption": caption,
#                 "likes": 0,
#                 "comments": [],
#                 "timestamp": datetime.now()
#             }
#             posts.insert(0, post)  # newest first
#             return redirect(url_for("home"))

#     return render_template("uploads.html")

# # @app.route('/comment/<int:post_id>', methods=['POST'])
# # # @login_required
# # def add_comment(post_id):
# #     content = request.form.get("content", "").strip()
# #     if not content:
# #         flash("Comment cannot be empty!", "danger")
# #         return redirect(url_for("home"))

#     # comment = Comment(content=content, user_id=current_user.id, post_id=post_id)
#     # db.session.add(comment)
#     # db.session.commit()
#     # return redirect(url_for("home"))



# @app.route("/comments/<int:post_id>")
# def get_comments(post_id):
#     post = Post.query.get_or_404(post_id)
#     comments = [
#         {
#             "id":c.id,
#             "content":c.content,
#             "username": c.user.username,
#             "timestamp":time_since(c.timestamp)
#         }
#         for c in post.comments

#     ]
#     return jsonify({"comments": comments})



# @app.route("/comments/<int:post_id>", methods=["POST"])
# def add_comment(post_id):
#     data = request.get_json()
#     content = data .get("content","").strip()
#     if not content:
#         return jsonify({"error":"Empty Comment"}),400
    
#     post =Post.query.get_or_404(post_id)
#     user = User.query.first()

#     comment = Comment(content=content, user_id=user.id, post_id=post.id)
#     db.session.add(comment)
#     db.session.commit()

#     return {"message": "Comment added", "post_id": post.id}, 201

# # Make time_since function available in templates
# @app.context_processor
# def utility_processor():
#     return dict(time_since=time_since)

# # Run app
# if __name__ == '__main__':
#     socketio.run(app, debug=True)



# VERSION 2

# import os
# from datetime import datetime
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# from werkzeug.utils import secure_filename
# from flask_socketio import SocketIO
# from models import db, Post, User, Comment

# # Create Flask app
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'supersecretkey'
# app.config['UPLOAD_FOLDER'] = 'static/uploads'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Initialize extensions
# db.init_app(app)
# socketio = SocketIO(app)

# # Create DB tables and sample data
# with app.app_context():
#     db.create_all()
    
#     # Create a default user if none exists
#     if not User.query.first():
#         default_user = User(
#             username='Jīvanapāṭhaḥ' 
#         )
#         db.session.add(default_user)
#         db.session.commit()
#         print("Created default user")

# def time_since(post_time):
#     """
#     Helper function to convert datetime to human-readable format
#     Examples: "2 minutes ago", "3 hours ago", "Sep 14"
#     """
#     now = datetime.utcnow()
#     diff = now - post_time
#     seconds = int(diff.total_seconds())
#     minutes = seconds // 60
#     hours = minutes // 60
#     days = diff.days

#     if seconds < 60:
#         return f"{seconds} second{'s' if seconds != 1 else ''} ago"
#     elif minutes < 60:
#         return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
#     elif hours < 24:
#         return f"{hours} hour{'s' if hours != 1 else ''} ago"
#     elif days < 7:
#         return f"{days} day{'s' if days != 1 else ''} ago"
#     else:
#         return post_time.strftime("%b %d")

# @app.route('/')
# def home():
#     """
#     Home route that displays all posts from database
#     - Fetches all posts ordered by newest first
#     - Passes posts to template for rendering
#     """
#     posts = Post.query.order_by(Post.timestamp.desc()).all()
#     return render_template("index.html", posts=posts)

# @app.route("/upload", methods=["GET", "POST"])
# def upload_post():
#     """
#     Upload route for creating new posts
#     GET: Shows upload form
#     POST: Processes form data and creates new post in database
#     """
#     if request.method == "POST":
#         image = request.files['image']
#         caption = request.form["caption"]

#         if image and image.filename:
#             # Secure the filename to prevent directory traversal attacks
#             filename = secure_filename(image.filename)
#             filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            
#             # Ensure upload directory exists
#             os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
#             image.save(filepath)

#             # Get default user (in real app, use current_user)
#             user = User.query.first()
            
#             # Create new post in database
#             post = Post(
#                 caption=caption,
#                 image=filename,
#                 user_id=user.id
#             )
            
#             db.session.add(post)
#             db.session.commit()
            
#             flash("Post uploaded successfully!", "success")
#             return redirect(url_for("home"))
#         else:
#             flash("Please select an image!", "danger")

#     return render_template("uploads.html")

# @app.route("/comments/<int:post_id>")
# def get_comments(post_id):
#     post = Post.query.get_or_404(post_id)
    
#     # Fix: Use Comment.query instead of post.comments.order_by()
#     comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.asc()).all()
    
#     comments_data = [
#         {
#             "id": c.id,
#             "content": c.content,
#             "username": c.user.username,
#             "timestamp": time_since(c.timestamp)
#         }
#         for c in comments
#     ]
#     return jsonify({"comments": comments_data})

# @app.route("/comments/<int:post_id>", methods=["POST"])
# def add_comment(post_id):
#     """
#     API endpoint to add a new comment to a post
#     Expects JSON data with comment content
#     Returns success/error response
#     """
#     data = request.get_json()
#     content = data.get("content", "").strip()
    
#     if not content:
#         return jsonify({"error": "Comment cannot be empty"}), 400
    
#     post = Post.query.get_or_404(post_id)
#     user = User.query.first()  # In real app, use current_user
    
#     # Create new comment
#     comment = Comment(
#         content=content, 
#         user_id=user.id, 
#         post_id=post.id
#     )
    
#     db.session.add(comment)
#     db.session.commit()
    
#     return jsonify({
#         "message": "Comment added successfully",
#         "comment": {
#             "id": comment.id,
#             "content": comment.content,
#             "username": comment.user.username,
#             "timestamp": time_since(comment.timestamp)
#         }
#     }), 201

# # Make time_since function available in templates
# @app.context_processor
# def utility_processor():
#     """
#     Makes helper functions available in all templates
#     """
#     return dict(time_since=time_since)

# # Error handlers
# @app.errorhandler(404)
# def not_found(error):
#     return jsonify({"error": "Resource not found"}), 404

# @app.errorhandler(500)
# def internal_error(error):
#     db.session.rollback()
#     return jsonify({"error": "Internal server error"}), 500

# # Run app
# if __name__ == '__main__':
#     socketio.run(app, debug=True)


# VERSION 3 (Updated with AI)
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from models import db, Post, User, Comment

# Import the AI comment filter
from comment_filter import filter_comment_list, analyze_comment_text

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
socketio = SocketIO(app)

# Create DB tables and sample data
with app.app_context():
    db.create_all()
    
    # Create a default user if none exists
    if not User.query.first():
        default_user = User(
            username='Jīvanapāṭhaḥ' 
        )
        db.session.add(default_user)
        db.session.commit()
        print("Created default user")

def time_since(post_time):
    """
    Helper function to convert datetime to human-readable format
    Examples: "2 minutes ago", "3 hours ago", "Sep 14"
    """
    now = datetime.utcnow()
    diff = now - post_time
    seconds = int(diff.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = diff.days

    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"
    elif minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif days < 7:
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return post_time.strftime("%b %d")
    
def clean_json(obj):
    """Recursively convert NumPy types to Python native types."""
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]
    elif hasattr(obj, "item") and callable(obj.item):  # numpy scalar
        return obj.item()
    elif type(obj).__name__ in ["bool_", "int_", "float_"]:  # numpy dtypes
        return obj.tolist()
    return obj

@app.route('/')
def home():
    """
    Home route that displays all posts from database
    - Fetches all posts ordered by newest first
    - Passes posts to template for rendering
    """
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("index.html", posts=posts)

@app.route("/upload", methods=["GET", "POST"])
def upload_post():
    """
    Upload route for creating new posts
    GET: Shows upload form
    POST: Processes form data and creates new post in database
    """
    if request.method == "POST":
        image = request.files['image']
        caption = request.form["caption"]

        if image and image.filename:
            # Secure the filename to prevent directory traversal attacks
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            
            # Ensure upload directory exists
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image.save(filepath)

            # Get default user (in real app, use current_user)
            user = User.query.first()
            
            # Create new post in database
            post = Post(
                caption=caption,
                image=filename,
                user_id=user.id
            )
            
            db.session.add(post)
            db.session.commit()
            
            flash("Post uploaded successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("Please select an image!", "danger")

    return render_template("uploads.html")

@app.route("/comments/<int:post_id>")
def get_comments(post_id):
    """
    Get comments with optional AI filtering
    ?filter=ai to enable AI filtering
    """
    post = Post.query.get_or_404(post_id)
    use_ai_filter = request.args.get('filter') == 'ai'
    
    # Get all comments
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.asc()).all()
    
    comments_data = [
        {
            "id": c.id,
            "content": c.content,
            "username": c.user.username,
            "timestamp": time_since(c.timestamp)
        }
        for c in comments
    ]
    
    # Apply AI filtering if requested
    if use_ai_filter:
        filtered_comments = filter_comment_list(comments_data)
        return jsonify(clean_json({
            "comments": filtered_comments,
            "total_original": len(comments_data),
            "total_filtered": len(filtered_comments),
            "ai_filtered": True
        }))
    
    return jsonify(clean_json({
    "comments": comments_data,
    "ai_filtered": False
    }))
    

@app.route("/comments/<int:post_id>/analyze", methods=["POST"])
def analyze_comment_before_post(post_id):
    """
    Analyze comment before posting to warn user
    Real-time preview as user types
    """
    data = request.get_json()
    content = data.get("content", "").strip()
    
    if not content:
        return jsonify({"error": "Empty comment"}), 400
    
    # Analyze the comment
    analysis = analyze_comment_text(content)
    
    return jsonify(clean_json({
    "analysis": analysis,
    "content": content,
    "post_id": post_id
    }))

@app.route("/comments/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    """
    Enhanced add comment with AI analysis
    """
    data = request.get_json()
    content = data.get("content", "").strip()
    force_post = data.get("force_post", False)  # Allow user to override AI warning
    
    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400
    
    post = Post.query.get_or_404(post_id)
    user = User.query.first()  # In real app, use current_user
    
    if not user:
        return jsonify({"error": "No user found"}), 400
    
    # Analyze comment before saving
    analysis = analyze_comment_text(content)
    
    # If comment is inappropriate and user hasn't forced it
    if not analysis['should_display'] and not force_post:
        return jsonify({
            "warning": True,
            "message": "AI detected potential issues with your comment",
            "reasons": analysis['reasons'],
            "analysis": analysis['analysis'],
            "suggestion": "Consider rephrasing your comment to be more positive and constructive."
        }), 422  # Unprocessable Entity
    
    # Create new comment (even if flagged, but user can choose to filter it out)
    comment = Comment(
        content=content,
        user_id=user.id,
        post_id=post.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        "message": "Comment added successfully",
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "username": comment.user.username,
            "timestamp": time_since(comment.timestamp)
        },
        "ai_analysis": analysis if not analysis['should_display'] else None
    }), 201

# Make time_since function available in templates
@app.context_processor
def utility_processor():
    """
    Makes helper functions available in all templates
    """
    return dict(time_since=time_since)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

# Run app
if __name__ == '__main__':
    socketio.run(app, debug=True)