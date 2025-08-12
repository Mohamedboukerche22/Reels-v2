import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import desc, func
from app import app, db
from models import User, Video, Like, Comment, Follow
import uuid


def allowed_file(filename):
    """Check if file extension is allowed for video uploads"""
    ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Homepage with video reels feed"""
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    # Get videos for the feed (ordered by most recent)
    videos = Video.query.filter_by(is_active=True).order_by(desc(Video.created_at)).limit(20).all()
    
    return render_template('index.html', videos=videos)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and password and check_password_hash(user.password_hash, password):
            if not user.is_active():
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('login'))
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        full_name = request.form.get('full_name')
        password = request.form.get('password')
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return render_template('register.html')
        
        if not password:
            flash('Password is required.', 'danger')
            return render_template('register.html')
            
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            password_hash=generate_password_hash(password)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_video():
    """Upload a new video"""
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file selected.', 'danger')
            return redirect(request.url)
        
        file = request.files['video']
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if file.filename == '':
            flash('No video file selected.', 'danger')
            return redirect(request.url)
        
        if not title:
            flash('Video title is required.', 'danger')
            return redirect(request.url)
        
        if file and file.filename and allowed_file(file.filename):
            # Generate unique filename
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            
            # Create videos directory if it doesn't exist
            videos_dir = os.path.join(os.getcwd(), 'videos')
            if not os.path.exists(videos_dir):
                os.makedirs(videos_dir)
            
            file_path = os.path.join(videos_dir, filename)
            file.save(file_path)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            # Create video record
            video = Video(
                user_id=current_user.id,
                title=title,
                filename=filename,
                description=description,
                file_size=file_size
            )
            
            db.session.add(video)
            db.session.commit()
            
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Please upload MP4, WebM, MOV, or AVI files.', 'danger')
    
    return render_template('upload.html')


@app.route('/video/<filename>')
def serve_video(filename):
    """Serve video files"""
    videos_dir = os.path.join(os.getcwd(), 'videos')
    return send_from_directory(videos_dir, filename)


@app.route('/api/videos')
def api_videos():
    """API endpoint to get videos as JSON"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    videos = Video.query.filter_by(is_active=True)\
                       .order_by(desc(Video.created_at))\
                       .paginate(page=page, per_page=per_page, error_out=False)
    
    video_list = []
    for video in videos.items:
        video_data = {
            'id': video.id,
            'title': video.title,
            'description': video.description,
            'filename': video.filename,
            'video_url': url_for('serve_video', filename=video.filename),
            'user': {
                'id': video.user.id,
                'username': video.user.username,
                'full_name': video.user.full_name
            },
            'stats': {
                'views_count': video.views_count,
                'likes_count': video.likes_count,
                'comments_count': video.comments_count,
                'shares_count': video.shares_count
            },
            'created_at': video.created_at.isoformat()
        }
        video_list.append(video_data)
    
    return jsonify({
        'videos': video_list,
        'has_next': videos.has_next,
        'has_prev': videos.has_prev,
        'next_num': videos.next_num,
        'prev_num': videos.prev_num,
        'page': videos.page,
        'pages': videos.pages,
        'total': videos.total
    })


@app.route('/api/like/<int:video_id>', methods=['POST'])
@login_required
def toggle_like(video_id):
    """Toggle like on a video"""
    video = Video.query.get_or_404(video_id)
    
    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()
    
    if existing_like:
        # Remove like
        db.session.delete(existing_like)
        video.likes_count = max(0, video.likes_count - 1)
        liked = False
    else:
        # Add like
        like = Like(user_id=current_user.id, video_id=video_id)
        db.session.add(like)
        video.likes_count += 1
        liked = True
    
    db.session.commit()
    
    return jsonify({
        'liked': liked,
        'likes_count': video.likes_count
    })


@app.route('/api/comment/<int:video_id>', methods=['POST'])
@login_required
def add_comment(video_id):
    """Add a comment to a video"""
    video = Video.query.get_or_404(video_id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    comment = Comment(
        user_id=current_user.id,
        video_id=video_id,
        content=content
    )
    
    db.session.add(comment)
    video.comments_count += 1
    db.session.commit()
    
    return jsonify({
        'id': comment.id,
        'content': comment.content,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'full_name': current_user.full_name
        },
        'created_at': comment.created_at.isoformat()
    })


@app.route('/api/comments/<int:video_id>')
def get_comments(video_id):
    """Get comments for a video"""
    comments = Comment.query.filter_by(video_id=video_id)\
                          .order_by(desc(Comment.created_at))\
                          .limit(50).all()
    
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'content': comment.content,
            'user': {
                'id': comment.user.id,
                'username': comment.user.username,
                'full_name': comment.user.full_name
            },
            'created_at': comment.created_at.isoformat()
        })
    
    return jsonify({'comments': comments_data})


@app.route('/profile/<username>')
@login_required
def user_profile(username):
    """User profile page"""
    user = User.query.filter_by(username=username).first_or_404()
    videos = Video.query.filter_by(user_id=user.id, is_active=True)\
                       .order_by(desc(Video.created_at))\
                       .limit(20).all()
    
    return render_template('profile.html', user=user, videos=videos)


@app.route('/api/view/<int:video_id>', methods=['POST'])
def increment_view_count(video_id):
    """Increment view count for a video"""
    video = Video.query.get_or_404(video_id)
    video.views_count += 1
    db.session.commit()
    
    return jsonify({'views_count': video.views_count})
