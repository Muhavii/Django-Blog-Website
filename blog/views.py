import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Post, Comment, Like, Profile
from .forms import PostForm, CommentForm, UserRegistrationForm, UserUpdateForm, ProfileUpdateForm, UserSearchForm


def home(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'posts': page_obj,
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
def like_post(request, pk):
    if request.method == 'POST':
        post = get_object_or_404(Post, pk=pk)
        is_like = request.POST.get('is_like') == 'true'
        
        # Get or create like object
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={'is_like': is_like}
        )
        
        if not created:
            # If like exists, update or delete
            if like.is_like == is_like:
                # Same vote, remove it
                like.delete()
                action = 'removed'
            else:
                # Different vote, update it
                like.is_like = is_like
                like.save()
                action = 'updated'
        else:
            action = 'added'
        
        # Return JSON response for AJAX
        return JsonResponse({
            'success': True,
            'like_count': post.get_like_count(),
            'dislike_count': post.get_dislike_count(),
            'user_vote': like_obj.is_like if like_obj else None
        })
    
    return JsonResponse({'success': False})


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
        profile = get_object_or_404(Profile, user=user)
        
        # Check if the current user can view this profile
        if not profile.can_view_profile(request.user):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please log in to view this profile.')
                return redirect('login') + f'?next={request.path}'
            messages.error(request, 'You do not have permission to view this profile.')
            return redirect('home')
        
        # Get profile picture URL with error handling
        profile_picture_url = profile.get_profile_picture_url()
        
        # Get user's public posts (only show published posts to non-owners)
        user_posts = Post.objects.filter(author=user)
        if request.user != user:  # Only show published posts to non-owners
            user_posts = user_posts.filter(status='published')
        user_posts = user_posts.order_by('-created_at')[:5]
        
        # Prepare social links if available
        social_links = {}
        if profile.website:
            social_links['Website'] = profile.website
        if profile.twitter_handle:
            social_links['Twitter'] = f'https://twitter.com/{profile.twitter_handle}'
        if profile.github_username:
            social_links['GitHub'] = f'https://github.com/{profile.github_username}'
        
        context = {
            'profile_user': user,
            'profile': profile,
            'profile_picture_url': profile_picture_url,
            'user_posts': user_posts,
            'post_count': user_posts.count(),
            'social_links': social_links,
            'can_edit': request.user == user,
            'is_owner': request.user == user,
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
