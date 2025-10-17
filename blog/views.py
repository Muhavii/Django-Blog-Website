import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods

# Set up logging
logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
import os
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Post, Comment, Like, Profile
from .forms import PostForm, CommentForm, UserRegistrationForm, UserUpdateForm, ProfileUpdateForm, UserSearchForm


def home(request):
    # Debug: Log request
    logger.info("Home view accessed")
    
    # Get featured posts (most viewed and most liked)
    featured_posts = Post.objects.annotate(
        like_count=Count('likes', filter=Q(likes__is_like=True))
    ).order_by('-view_count', '-like_count')[:2]
    
    # Debug: Log featured posts count
    logger.info(f"Found {len(featured_posts)} featured posts")
    
    # Get all posts with related data to avoid N+1 queries
    posts = Post.objects.select_related('author', 'author__profile').prefetch_related('comments').annotate(
        like_count=Count('likes', filter=Q(likes__is_like=True)),
        comment_count=Count('comments')
    ).order_by('-created_at')
    
    # Debug: Log total posts count
    logger.info(f"Found {posts.count()} total posts")
    
    # Pagination
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Debug: Log pagination info
    logger.info(f"Page {page_obj.number} of {paginator.num_pages}, showing {len(page_obj)} posts")
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj,  # This is the paginated queryset
        'featured_posts': featured_posts,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'blog/home.html', context)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Your comment has been added!')
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/post_detail.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Your post has been created!')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    
    context = {'form': form}
    return render(request, 'blog/create_post.html', context)


@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the author
    if post.author != request.user:
        messages.error(request, 'You can only edit your own posts!')
        return redirect('post_detail', pk=post.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your post has been updated!')
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    
    context = {'form': form, 'post': post}
    return render(request, 'blog/edit_post.html', context)


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is the author
    if post.author != request.user:
        messages.error(request, 'You can only delete your own posts!')
        return redirect('post_detail', pk=post.pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted!')
        return redirect('home')
    
    context = {'post': post}
    return render(request, 'blog/delete_post.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'blog/register.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        from django.contrib.auth import authenticate, login
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'blog/login.html')


@login_required
def like_post(request, post_id):
    """Handle like/dislike actions via AJAX with optimized performance."""
    if request.method != 'POST':
        return JsonResponse(
            {'success': False, 'error': 'Invalid request method'}, 
            status=405
        )
    
    try:
        # Get the post with minimal fields needed
        post = get_object_or_404(Post.objects.only('id'), pk=post_id)
        is_like_param = request.POST.get('is_like', '').lower()
        
        with transaction.atomic():
            # Start with base queryset
            like_qs = Like.objects.select_for_update().filter(
                user=request.user,
                post=post
            )
            
            # Get existing like if it exists
            existing_like = like_qs.first()
            
            # Handle toggle off (empty is_like parameter)
            if is_like_param == '':
                if existing_like:
                    existing_like.delete()
                
                # Get updated counts in a single optimized query
                counts = Like.objects.filter(post=post).aggregate(
                    like_count=Count('id', filter=Q(is_like=True)),
                    dislike_count=Count('id', filter=Q(is_like=False))
                )
                
                return JsonResponse({
                    'success': True,
                    'like_count': counts['like_count'],
                    'dislike_count': counts['dislike_count'],
                    'user_vote': None
                })
            
            # Handle like/dislike
            is_like = is_like_param == 'true'
            
            if existing_like:
                if existing_like.is_like == is_like:
                    # Toggle off
                    existing_like.delete()
                    user_vote = None
                else:
                    # Toggle between like/dislike
                    existing_like.is_like = is_like
                    existing_like.save(update_fields=['is_like'])
                    user_vote = is_like
            else:
                # Create new like
                Like.objects.create(
                    user=request.user,
                    post=post,
                    is_like=is_like
                )
                user_vote = is_like
            
            # Get updated counts using a single query
            counts = Like.objects.filter(post=post).aggregate(
                like_count=Count('id', filter=Q(is_like=True)),
                dislike_count=Count('id', filter=Q(is_like=False))
            )
            
            return JsonResponse({
                'success': True,
                'like_count': counts['like_count'],
                'dislike_count': counts['dislike_count'],
                'user_vote': user_vote
            })
            
    except Exception as e:
        logger.error(
            f"Error in like_post for post {post_id}: {str(e)}",
            exc_info=True,
            extra={
                'user': request.user.id if request.user.is_authenticated else None,
                'post': post_id,
                'is_like': request.POST.get('is_like')
            }
        )
        return JsonResponse(
            {'success': False, 'error': 'An error occurred while processing your request.'},
            status=500
        )


@login_required
def profile_settings(request):
    """View for users to edit their profile settings"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                import logging
                logger = logging.getLogger(__name__)
                
                # Log before saving
                logger.info(f"Saving profile for user: {request.user.username}")
                
                # Save user data first
                user = user_form.save(commit=False)
                user.save()
                
                # Handle profile
                profile = profile_form.save(commit=False)
                
                # Check if a new profile picture was uploaded
                if 'profile_picture' in request.FILES:
                    logger.info("New profile picture detected in request.FILES")
                    
                    # Get the old picture before saving
                    old_picture = None
                    if hasattr(profile, 'profile_picture') and profile.profile_picture:
                        old_picture = profile.profile_picture
                        logger.info(f"Old picture URL: {old_picture.url if hasattr(old_picture, 'url') else 'No URL'}")
                    
                    # Save the profile to get the new file path
                    profile.save()
                    
                    # Log the new picture details
                    if hasattr(profile.profile_picture, 'url'):
                        logger.info(f"New picture URL after save: {profile.profile_picture.url}")
                    
                    # If there was an old picture and it's different from the new one, delete it
                    if old_picture and (not hasattr(profile.profile_picture, 'url') or 
                                      old_picture.url != profile.profile_picture.url):
                        try:
                            logger.info("Attempting to delete old profile picture")
                            old_picture.delete(save=False)
                            logger.info("Successfully deleted old profile picture")
                        except Exception as e:
                            logger.error(f"Error deleting old profile picture: {str(e)}")
                else:
                    # No new picture, just save the profile
                    profile.save()
                
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('profile_settings')
                
            except Exception as e:
                logger.error(f"Error in profile_settings view: {str(e)}", exc_info=True)
                messages.error(request, f'Error updating profile. Please try again. Error: {str(e)}')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Add debug information to context
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'debug': {
            'has_profile': hasattr(request.user, 'profile'),
            'has_picture': hasattr(request.user, 'profile') and bool(request.user.profile.profile_picture),
            'picture_url': request.user.profile.get_profile_picture_url() if hasattr(request.user, 'profile') else 'No profile',
        }
    }
    return render(request, 'blog/profile_settings.html', context)


def profile_view(request, username):
    """View to display a user's profile with privacy controls"""
    logger = logging.getLogger(__name__)
    logger.info(f"Profile view called for username: {username}")
    
    try:
        from django.contrib.auth.models import User
        user = get_object_or_404(User, username=username)
        
        # Get or create profile if it doesn't exist with safe defaults
        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                'privacy_setting': 'public',
                'bio': ''
            }
        )
        
        # Ensure profile has all required fields
        if not hasattr(profile, 'privacy_setting') or not profile.privacy_setting:
            profile.privacy_setting = 'public'
            profile.save()
        
        # Check if the current user can view this profile
        if not profile.can_view_profile(request.user):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to view this profile.')
                return redirect('login') + f'?next={request.path}'
            messages.error(request, 'You do not have permission to view this profile.')
            return redirect('home')
        
        # Get profile picture URL with error handling
        try:
            profile_picture_url = profile.get_profile_picture_url()
        except Exception as e:
            logger.error(f"Error getting profile picture URL: {str(e)}")
            profile_picture_url = '/static/images/default-avatar.png'
        
        # Get user's posts (show all posts to the owner, limit to 5 most recent)
        try:
            user_posts = Post.objects.filter(author=user).order_by('-created_at')
            if request.user != user:  # For non-owners, only show posts with an image
                user_posts = user_posts.exclude(image__isnull=True).exclude(image='')
            user_posts = list(user_posts[:5])  # Convert to list after slicing
            post_count = len(user_posts)  # Use len() since we have a list now
        except Exception as e:
            logger.error(f"Error getting user posts: {str(e)}")
            user_posts = []
            post_count = 0
        
        # Prepare social links if available
        social_links = {}
        try:
            if hasattr(profile, 'website') and profile.website:
                social_links['Website'] = profile.website
            if hasattr(profile, 'twitter_handle') and profile.twitter_handle:
                social_links['Twitter'] = f'https://twitter.com/{profile.twitter_handle}'
            if hasattr(profile, 'github_username') and profile.github_username:
                social_links['GitHub'] = f'https://github.com/{profile.github_username}'
            # Add new social media fields
            if hasattr(profile, 'facebook_url') and profile.facebook_url:
                social_links['Facebook'] = profile.facebook_url
            if hasattr(profile, 'instagram_username') and profile.instagram_username:
                social_links['Instagram'] = f'https://instagram.com/{profile.instagram_username}'
            if hasattr(profile, 'tiktok_username') and profile.tiktok_username:
                social_links['TikTok'] = f'https://tiktok.com/@{profile.tiktok_username}'
            if hasattr(profile, 'snapchat_username') and profile.snapchat_username:
                social_links['Snapchat'] = f'https://snapchat.com/add/{profile.snapchat_username}'
        except Exception as e:
            logger.error(f"Error getting social links: {str(e)}")
        
        # Get follow data
        is_following = False
        if request.user.is_authenticated and request.user != user:
            from .models import Follow
            is_following = Follow.objects.filter(
                follower=request.user, 
                following=user
            ).exists()
            
        # Get followers and following counts
        followers_count = user.followers.count()
        following_count = user.following.count()
        
        context = {
            'profile_user': user,
            'profile': profile,
            'profile_picture_url': profile_picture_url,
            'user_posts': user_posts,
            'post_count': post_count,
            'social_links': social_links,
            'can_edit': request.user == user,
            'is_owner': request.user == user,
            'is_following': is_following,
            'followers_count': followers_count,
            'following_count': following_count,
        }
        
        return render(request, 'blog/profile_view.html', context)
        
    except Exception as e:
        logger.error(f"Error in profile_view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while loading the profile.')
        return redirect('home')


def user_logout(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
@require_POST
def follow_user(request, username):
    """View to follow/unfollow a user"""
    try:
        user_to_follow = get_user_model().objects.get(username=username)
        if request.user == user_to_follow:
            return JsonResponse({'error': 'You cannot follow yourself'}, status=400)
        
        from .models import Follow
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if not created:
            follow.delete()
            return JsonResponse({'status': 'unfollowed', 'count': user_to_follow.followers.count()})
            
        return JsonResponse({'status': 'followed', 'count': user_to_follow.followers.count()})
        
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_user_data(user):
    """Helper function to get user data for JSON response"""
    try:
        avatar_url = user.profile.profile_picture.url if user.profile.profile_picture else ''
    except:
        avatar_url = os.path.join(settings.STATIC_URL, 'images/default-avatar.png')
    
    return {
        'username': user.username,
        'full_name': user.get_full_name(),
        'avatar': request.build_absolute_uri(avatar_url) if avatar_url else ''
    }


def followers_list(request, username):
    """View to get list of followers for a user"""
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        user = get_user_model().objects.get(username=username)
        followers = user.followers.all().select_related('follower')
        
        followers_data = [{
            'username': follow.follower.username,
            'full_name': follow.follower.get_full_name(),
            'avatar': request.build_absolute_uri(follow.follower.profile.profile_picture.url) if hasattr(follow.follower, 'profile') and follow.follower.profile.profile_picture else ''
        } for follow in followers]
        
        return JsonResponse(followers_data, safe=False)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def following_list(request, username):
    """View to get list of users that the given user is following"""
    if not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    try:
        user = get_user_model().objects.get(username=username)
        following = user.following.all().select_related('following')
        
        following_data = [{
            'username': follow.following.username,
            'full_name': follow.following.get_full_name(),
            'avatar': request.build_absolute_uri(follow.following.profile.profile_picture.url) if hasattr(follow.following, 'profile') and follow.following.profile.profile_picture else ''
        } for follow in following]
        
        return JsonResponse(following_data, safe=False)
    except get_user_model().DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def followers_modal(request, username):
    """View to display followers in a modal"""
    user = get_object_or_404(get_user_model(), username=username)
    followers = user.followers.all().select_related('follower')
    return render(request, 'blog/includes/followers_modal.html', {
        'followers': followers,
        'profile_user': user
    })


def following_modal(request, username):
    """View to display following list in a modal"""
    user = get_object_or_404(get_user_model(), username=username)
    following = user.following.all().select_related('following')
    return render(request, 'blog/includes/following_modal.html', {
        'following': following,
        'profile_user': user
    })


def user_search(request):
    """View for searching users"""
    form = UserSearchForm(request.GET or None)
    users = []
    
    if form.is_valid() and form.cleaned_data.get('query'):
        query = form.cleaned_data['query']
        users = get_user_model().objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('profile').order_by('username')
        
        # Filter out users with private profiles if not the owner
        if not request.user.is_authenticated:
            users = users.filter(profile__privacy_setting='public')
        elif not request.user.is_superuser:  # Admins can see all users
            users = users.exclude(
                ~Q(profile__user=request.user) & 
                Q(profile__privacy_setting='private')
            )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 10)  # 10 users per page
    
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    
    return render(request, 'blog/user_search.html', {
        'form': form,
        'users': users,
        'query': request.GET.get('query', '')
    })


def handler404(request, exception, template_name='errors/404.html'):
    """
    Custom 404 error handler
    """
    response = render(request, template_name, status=404)
    response.status_code = 404
    return response


def handler500(request, template_name='errors/500.html'):
    """
    Custom 500 error handler
    """
    response = render(request, template_name, status=500)
    response.status_code = 500
    return response
