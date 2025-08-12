// Moh-Reels JavaScript
class ReelsApp {
    constructor() {
        this.currentVideoId = null;
        this.currentPage = 1;
        this.isLoading = false;
        this.observer = null;
        
        this.init();
    }
    
    init() {
        this.setupIntersectionObserver();
        this.setupVideoControls();
        this.setupLikeButtons();
        this.setupCommentButtons();
        this.setupLoadMoreButton();
        this.setupCommentModal();
        
        // Auto-play first video
        this.playFirstVideo();
    }
    
    setupIntersectionObserver() {
        const options = {
            root: null,
            rootMargin: '-50% 0px -50% 0px',
            threshold: 0
        };
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const video = entry.target.querySelector('.reel-video');
                const videoId = entry.target.getAttribute('data-video-id');
                
                if (entry.isIntersecting) {
                    this.playVideo(video, videoId);
                } else {
                    this.pauseVideo(video);
                }
            });
        }, options);
        
        // Observe all reel items
        document.querySelectorAll('.reel-item').forEach(item => {
            this.observer.observe(item);
        });
    }
    
    playVideo(video, videoId) {
        if (video && video.paused) {
            video.play().catch(e => console.log('Video play failed:', e));
            this.currentVideoId = videoId;
            
            // Increment view count
            this.incrementViewCount(videoId);
        }
    }
    
    pauseVideo(video) {
        if (video && !video.paused) {
            video.pause();
        }
    }
    
    playFirstVideo() {
        const firstReel = document.querySelector('.reel-item');
        if (firstReel) {
            const video = firstReel.querySelector('.reel-video');
            const videoId = firstReel.getAttribute('data-video-id');
            if (video) {
                this.playVideo(video, videoId);
            }
        }
    }
    
    setupVideoControls() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('reel-video')) {
                const video = e.target;
                if (video.paused) {
                    video.play();
                } else {
                    video.pause();
                }
            }
        });
        
        // Add double-tap to like on mobile
        let tapCount = 0;
        let tapTimer = null;
        
        document.addEventListener('touchend', (e) => {
            if (e.target.classList.contains('reel-video')) {
                tapCount++;
                if (tapCount === 1) {
                    tapTimer = setTimeout(() => {
                        tapCount = 0;
                    }, 300);
                } else if (tapCount === 2) {
                    clearTimeout(tapTimer);
                    tapCount = 0;
                    
                    // Double tap - like video
                    const reelItem = e.target.closest('.reel-item');
                    const videoId = reelItem.getAttribute('data-video-id');
                    this.toggleLike(videoId);
                    
                    // Show heart animation
                    this.showLikeAnimation(e.touches[0].clientX, e.touches[0].clientY);
                }
            }
        });
    }
    
    setupLikeButtons() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.like-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.like-btn');
                const videoId = btn.getAttribute('data-video-id');
                this.toggleLike(videoId);
            }
        });
    }
    
    async toggleLike(videoId) {
        try {
            const response = await fetch(`/api/like/${videoId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                const likeBtn = document.querySelector(`.like-btn[data-video-id="${videoId}"]`);
                const icon = likeBtn.querySelector('i');
                const count = likeBtn.querySelector('.count');
                
                if (data.liked) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    likeBtn.classList.add('liked');
                } else {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    likeBtn.classList.remove('liked');
                }
                
                count.textContent = data.likes_count;
            }
        } catch (error) {
            console.error('Error toggling like:', error);
        }
    }
    
    showLikeAnimation(x, y) {
        const heart = document.createElement('div');
        heart.innerHTML = '<i class="fas fa-heart"></i>';
        heart.style.cssText = `
            position: fixed;
            left: ${x - 25}px;
            top: ${y - 25}px;
            font-size: 50px;
            color: #ff0050;
            z-index: 9999;
            pointer-events: none;
            animation: likeAnimation 1s ease-out forwards;
        `;
        
        document.body.appendChild(heart);
        
        setTimeout(() => {
            document.body.removeChild(heart);
        }, 1000);
    }
    
    setupCommentButtons() {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.comment-btn')) {
                e.preventDefault();
                const btn = e.target.closest('.comment-btn');
                const videoId = btn.getAttribute('data-video-id');
                this.showComments(videoId);
            }
        });
    }
    
    async showComments(videoId) {
        try {
            const response = await fetch(`/api/comments/${videoId}`);
            const data = await response.json();
            
            if (response.ok) {
                this.displayComments(data.comments);
                
                // Set current video ID for commenting
                const modal = document.getElementById('comment-modal');
                modal.setAttribute('data-video-id', videoId);
                
                // Show modal
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        } catch (error) {
            console.error('Error fetching comments:', error);
        }
    }
    
    displayComments(comments) {
        const container = document.getElementById('comments-container');
        container.innerHTML = '';
        
        if (comments.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No comments yet. Be the first to comment!</p>';
            return;
        }
        
        comments.forEach(comment => {
            const commentDiv = document.createElement('div');
            commentDiv.className = 'comment-item';
            commentDiv.innerHTML = `
                <div class="comment-user">@${comment.user.username}</div>
                <div class="comment-content">${this.escapeHtml(comment.content)}</div>
                <div class="comment-time">${this.formatDate(comment.created_at)}</div>
            `;
            container.appendChild(commentDiv);
        });
    }
    
    setupCommentModal() {
        const submitBtn = document.getElementById('submit-comment-btn');
        const commentInput = document.getElementById('comment-input');
        
        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                this.submitComment();
            });
        }
        
        if (commentInput) {
            commentInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.submitComment();
                }
            });
        }
    }
    
    async submitComment() {
        const modal = document.getElementById('comment-modal');
        const videoId = modal.getAttribute('data-video-id');
        const input = document.getElementById('comment-input');
        const content = input.value.trim();
        
        if (!content) {
            return;
        }
        
        try {
            const response = await fetch(`/api/comment/${videoId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Clear input
                input.value = '';
                
                // Refresh comments
                this.showComments(videoId);
                
                // Update comment count on button
                const commentBtn = document.querySelector(`.comment-btn[data-video-id="${videoId}"]`);
                if (commentBtn) {
                    const countSpan = commentBtn.querySelector('.count');
                    const currentCount = parseInt(countSpan.textContent) || 0;
                    countSpan.textContent = currentCount + 1;
                }
            } else {
                alert(data.error || 'Failed to add comment');
            }
        } catch (error) {
            console.error('Error submitting comment:', error);
            alert('Failed to add comment');
        }
    }
    
    async incrementViewCount(videoId) {
        try {
            await fetch(`/api/view/${videoId}`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Error incrementing view count:', error);
        }
    }
    
    setupLoadMoreButton() {
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadMoreVideos();
            });
        }
    }
    
    async loadMoreVideos() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const loadMoreBtn = document.getElementById('load-more-btn');
        const originalText = loadMoreBtn.textContent;
        loadMoreBtn.textContent = 'Loading...';
        loadMoreBtn.disabled = true;
        
        try {
            this.currentPage++;
            const response = await fetch(`/api/videos?page=${this.currentPage}`);
            const data = await response.json();
            
            if (response.ok && data.videos.length > 0) {
                this.appendVideos(data.videos);
                
                if (!data.has_next) {
                    loadMoreBtn.style.display = 'none';
                }
            } else {
                loadMoreBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading more videos:', error);
        } finally {
            this.isLoading = false;
            loadMoreBtn.textContent = originalText;
            loadMoreBtn.disabled = false;
        }
    }
    
    appendVideos(videos) {
        const feed = document.getElementById('reels-feed');
        
        videos.forEach(video => {
            const reelItem = this.createReelElement(video);
            feed.appendChild(reelItem);
            
            // Observe new reel item
            this.observer.observe(reelItem);
        });
    }
    
    createReelElement(video) {
        const reelItem = document.createElement('div');
        reelItem.className = 'reel-item';
        reelItem.setAttribute('data-video-id', video.id);
        
        reelItem.innerHTML = `
            <div class="video-container">
                <video class="reel-video" 
                       src="${video.video_url}"
                       muted
                       loop
                       preload="metadata">
                    Your browser does not support the video tag.
                </video>
                
                <div class="video-overlay">
                    <div class="video-info">
                        <div class="user-info">
                            <strong>@${video.user.username}</strong>
                            <p>${video.user.full_name}</p>
                        </div>
                        <div class="video-details">
                            <h3>${this.escapeHtml(video.title)}</h3>
                            ${video.description ? `<p class="description">${this.escapeHtml(video.description)}</p>` : ''}
                        </div>
                    </div>
                    
                    <div class="video-actions">
                        <button class="action-btn like-btn" data-video-id="${video.id}">
                            <i class="far fa-heart"></i>
                            <span class="count">${video.stats.likes_count}</span>
                        </button>
                        <button class="action-btn comment-btn" data-video-id="${video.id}">
                            <i class="far fa-comment"></i>
                            <span class="count">${video.stats.comments_count}</span>
                        </button>
                        <button class="action-btn share-btn" data-video-id="${video.id}">
                            <i class="far fa-share-square"></i>
                            <span class="count">${video.stats.shares_count}</span>
                        </button>
                        <div class="views-count">
                            <i class="fas fa-eye"></i>
                            <span>${video.stats.views_count}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return reelItem;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString();
    }
}

// Add CSS for like animation
const style = document.createElement('style');
style.textContent = `
    @keyframes likeAnimation {
        0% {
            opacity: 1;
            transform: scale(0) rotate(0deg);
        }
        50% {
            opacity: 1;
            transform: scale(1.2) rotate(-10deg);
        }
        100% {
            opacity: 0;
            transform: scale(1.4) rotate(0deg) translateY(-50px);
        }
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ReelsApp();
});

// Handle back/forward navigation
window.addEventListener('popstate', () => {
    location.reload();
});
