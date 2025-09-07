from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.utils import ProgrammingError, OperationalError

def admin_stats(request):
    if not request.path.startswith('/admin/'):
        return {}
    
    stats = {
        'posts_count': 0,
        'comments_count': 0,
        'users_count': 0,
    }
    recent_activity = []
    
    try:
        from blog.models import Post, Comment
        User = get_user_model()
        
        # Get basic stats
        stats.update({
            'posts_count': Post.objects.count(),
            'comments_count': Comment.objects.count(),
            'users_count': User.objects.count(),
        })
        
        # Add recent posts
        for post in Post.objects.order_by('-created_at')[:3]:
            recent_activity.append({
                'icon': 'file-alt',
                'message': f'New post: {post.title}',
                'time': post.created_at
            })
        
        # Add recent comments
        for comment in Comment.objects.select_related('post').order_by('-created_at')[:3]:
            recent_activity.append({
                'icon': 'comment',
                'message': f"New comment on '{getattr(comment.post, 'title', 'a post')}'",
                'time': comment.created_at
            })
        
        # Add recent users
        for user in User.objects.order_by('-date_joined')[:3]:
            recent_activity.append({
                'icon': 'user-plus',
                'message': f'New user: {user.username}',
                'time': user.date_joined
            })
        
        # Sort by time
        recent_activity.sort(key=lambda x: x['time'], reverse=True)
        
    except (ProgrammingError, OperationalError, ImportError) as e:
        # Handle case when tables don't exist yet
        pass
    
    return {
        'stats': stats,
        'recent_activity': recent_activity[:5]  # Show only 5 most recent
    }
