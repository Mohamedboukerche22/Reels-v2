from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255))
    followers_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)
    
    # Relationships
    videos = db.relationship('Video', backref='user', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, email, full_name, password_hash, bio=None):
        self.username = username
        self.email = email
        self.full_name = full_name
        self.password_hash = password_hash
        self.bio = bio
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_active(self):
        return self.active


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)  # bytes
    duration = db.Column(db.Integer)  # seconds
    thumbnail_url = db.Column(db.String(255))
    views_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    likes = db.relationship('Like', backref='video', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='video', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, title, filename, description=None, file_size=None):
        self.user_id = user_id
        self.title = title
        self.filename = filename
        self.description = description
        self.file_size = file_size
    
    def __repr__(self):
        return f'<Video {self.id}: {self.title}>'
    
    def get_file_path(self):
        return f"videos/{self.filename}"
    
    def get_video_url(self):
        return f"/video/{self.filename}"


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate likes
    __table_args__ = (db.UniqueConstraint('user_id', 'video_id', name='unique_user_video_like'),)
    
    def __init__(self, user_id, video_id):
        self.user_id = user_id
        self.video_id = video_id
    
    def __repr__(self):
        return f'<Like {self.user_id} -> {self.video_id}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id, video_id, content):
        self.user_id = user_id
        self.video_id = video_id
        self.content = content
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.user.username if self.user else "unknown"}>'


class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow'),)

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    followed = db.relationship('User', foreign_keys=[followed_id], backref='followers')
    
    def __repr__(self):
        return f'<Follow {self.follower_id} -> {self.followed_id}>'
