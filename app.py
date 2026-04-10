import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO
from models import db, Post, User, Comment

# Import the AI comment filter
from comment_filterv1 import filter_comment_list, analyze_comment_text

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
    if not User.query.first():
        default_user = User(username='Jīvanapāṭhaḥ')
        db.session.add(default_user)
        db.session.commit()
        print("Created default user")


def time_since(post_time):
    """Convert datetime to human-readable relative time."""
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
    elif hasattr(obj, "item") and callable(obj.item):
        return obj.item()
    elif type(obj).__name__ in ["bool_", "int_", "float_"]:
        return obj.tolist()
    return obj


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def home():
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template("index.html", posts=posts)


@app.route("/upload", methods=["GET", "POST"])
def upload_post():
    if request.method == "POST":
        image = request.files['image']
        caption = request.form["caption"]

        if image and image.filename:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            image.save(filepath)

            user = User.query.first()
            post = Post(caption=caption, image=filename, user_id=user.id)
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
    Fetch comments for a post.
    ?filter=ai  →  apply AI filtering (removes toxic/spam comments)
    """
    post = Post.query.get_or_404(post_id)
    use_ai_filter = request.args.get('filter') == 'ai'

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

    if use_ai_filter:
        filtered = filter_comment_list(comments_data)
        return jsonify(clean_json({
            "comments": filtered,
            "total_original": len(comments_data),
            "total_filtered": len(filtered),
            "ai_filtered": True
        }))

    return jsonify(clean_json({
        "comments": comments_data,
        "ai_filtered": False
    }))


@app.route("/comments/<int:post_id>/analyze", methods=["POST"])
def analyze_comment_before_post(post_id):
    """
    Real-time pre-post analysis endpoint.
    Returns verdict ('allow' | 'warn' | 'block'), sarcasm info, language detected, etc.
    Frontend can use this for live typing feedback.
    """
    data = request.get_json()
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"error": "Empty comment"}), 400

    analysis = analyze_comment_text(content)

    return jsonify(clean_json({
        "verdict": analysis.get("verdict"),          # 'allow' | 'warn' | 'block'
        "is_hard_block": analysis.get("is_hard_block"),
        "should_display": analysis.get("should_display"),
        "reasons": analysis.get("reasons", []),
        "analysis": analysis.get("analysis", {}),
        "content": content,
        "post_id": post_id
    }))


@app.route("/comments/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    """
    Add a comment with AI gate.

    Verdicts:
      allow  → save and return 201 immediately
      warn   → return 422 with warning; client may re-POST with force_post=true
      block  → return 403; no override allowed (genuinely toxic / multilingual abuse)
    """
    data = request.get_json()
    content = data.get("content", "").strip()
    force_post = data.get("force_post", False)

    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400

    post = Post.query.get_or_404(post_id)
    user = User.query.first()
    if not user:
        return jsonify({"error": "No user found"}), 400

    # Run AI analysis
    analysis = analyze_comment_text(content)
    verdict = analysis.get("verdict", "allow")
    is_hard_block = analysis.get("is_hard_block", False)

    # ---- BLOCK tier: no override ----
    if verdict == "block":
        return jsonify(clean_json({
            "error": "Comment blocked by AI moderation",
            "verdict": "block",
            "is_hard_block": True,
            "reasons": analysis["reasons"],
            "analysis": analysis["analysis"],
            "suggestion": (
                "Your comment was flagged as genuinely harmful and cannot be posted. "
                "Please rephrase it constructively."
            )
        })), 403  # Forbidden — no override

    # ---- WARN tier: allow force-post override ----
    if verdict == "warn" and not force_post:
        return jsonify(clean_json({
            "warning": True,
            "verdict": "warn",
            "is_hard_block": False,
            "message": "AI detected a potential issue with your comment",
            "reasons": analysis["reasons"],
            "analysis": analysis["analysis"],
            "suggestion": (
                "Consider rephrasing. If you believe this is a false positive, "
                "you can resubmit with force_post=true."
            )
        })), 422  # Unprocessable — user can override

    # ---- ALLOW or force-post after WARN ----
    comment = Comment(content=content, user_id=user.id, post_id=post.id)
    db.session.add(comment)
    db.session.commit()

    return jsonify(clean_json({
        "message": "Comment added successfully",
        "verdict": verdict,
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "username": comment.user.username,
            "timestamp": time_since(comment.timestamp)
        },
        # Only attach analysis payload if there was a warning override
        "ai_analysis": analysis if verdict == "warn" else None
    })), 201


# ---------------------------------------------------------------------------
# Delete Routes
# ---------------------------------------------------------------------------

@app.route("/comments/<int:comment_id>/delete", methods=["DELETE"])
def delete_comment(comment_id):
    """Delete a comment by ID. Only the comment owner can delete."""
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.first()

    if comment.user_id != user.id:
        return jsonify({"error": "Unauthorized"}), 403

    post_id = comment.post_id
    db.session.delete(comment)
    db.session.commit()

    return jsonify({
        "message": "Comment deleted successfully",
        "comment_id": comment_id,
        "post_id": post_id
    }), 200


@app.route("/posts/<int:post_id>/delete", methods=["DELETE"])
def delete_post(post_id):
    """Delete a post and all its comments. Cascades via SQLAlchemy relationship."""
    post = Post.query.get_or_404(post_id)
    user = User.query.first()

    if post.user_id != user.id:
        return jsonify({"error": "Unauthorized"}), 403

    try:
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], post.image)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception:
        pass

    db.session.delete(post)
    db.session.commit()

    return jsonify({
        "message": "Post deleted successfully",
        "post_id": post_id
    }), 200


# ---------------------------------------------------------------------------
# Context processors & error handlers
# ---------------------------------------------------------------------------

@app.context_processor
def utility_processor():
    return dict(time_since=time_since)


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))