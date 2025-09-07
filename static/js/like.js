// Main initialization when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeLikeButtons();
    initializeButtonStates();
});

// Initialize event listeners for like/dislike buttons
function initializeLikeButtons() {
    document.querySelectorAll('.like-btn, .dislike-btn').forEach(button => {
        button.addEventListener('click', handleButtonClick);
    });
}

// Handle button click events
function handleButtonClick(event) {
    const button = event.currentTarget;
    const isLike = button.classList.contains('like-btn');
    
    // Prevent multiple clicks
    if (button.disabled) return;
    
    // Check if clicking the same button that's already active (toggle off)
    const isActive = button.classList.contains('btn-success') || button.classList.contains('btn-danger');
    if (isActive) {
        // Toggle off by sending null vote
        handleVote(button, null);
    } else {
        // Handle like/dislike
        handleVote(button, isLike);
    }
}

// Initialize button states based on user's previous votes
function initializeButtonStates() {
    document.querySelectorAll('.like-btn, .dislike-btn').forEach(button => {
        const userVote = button.dataset.userVote;
        if (!userVote) return;
        
        const isLike = button.classList.contains('like-btn');
        if ((isLike && userVote === 'true') || (!isLike && userVote === 'false')) {
            updateButtonState(button, true);
        }
    });
}

// Handle the voting process with optimistic UI updates
async function handleVote(button, isLike) {
    const postId = button.dataset.postId;
    const csrfToken = getCSRFToken();
    
    if (!csrfToken) {
        showToast('Error: CSRF token not found', 'danger');
        return;
    }
    
    // Optimistic UI update - update UI immediately
    const buttons = document.querySelectorAll(`[data-post-id="${postId}"]`);
    const isLikeBtn = button.classList.contains('like-btn');
    const currentLikeCount = parseInt(document.querySelector(`.like-btn[data-post-id="${postId}"] .like-count`).textContent);
    const currentDislikeCount = parseInt(document.querySelector(`.dislike-btn[data-post-id="${postId}"] .dislike-count`).textContent);
    
    // Disable all buttons for this post
    buttons.forEach(btn => { btn.disabled = true; });
    
    // Optimistically update the UI
    if (isLike === null) {
        // Toggling off
        const activeButton = document.querySelector(`[data-post-id="${postId}"].btn-success, [data-post-id="${postId}"].btn-danger`);
        if (activeButton) {
            const isActiveLike = activeButton.classList.contains('like-btn');
            if (isActiveLike) {
                updateCounts(postId, Math.max(0, currentLikeCount - 1), currentDislikeCount);
            } else {
                updateCounts(postId, currentLikeCount, Math.max(0, currentDislikeCount - 1));
            }
            updateButtonState(activeButton, false);
        }
    } else {
        // Toggling between like/dislike
        const otherButton = document.querySelector(`[data-post-id="${postId}"]${isLikeBtn ? '.dislike-btn' : '.like-btn'}`);
        const isOtherActive = otherButton.classList.contains('btn-success') || otherButton.classList.contains('btn-danger');
        
        if (isOtherActive) {
            // Switching between like and dislike
            updateCounts(
                postId, 
                isLikeBtn ? currentLikeCount + 1 : Math.max(0, currentLikeCount - 1),
                isLikeBtn ? Math.max(0, currentDislikeCount - 1) : currentDislikeCount + 1
            );
            updateButtonState(otherButton, false);
        } else {
            // New like/dislike
            updateCounts(
                postId,
                isLikeBtn ? currentLikeCount + 1 : currentLikeCount,
                isLikeBtn ? currentDislikeCount : currentDislikeCount + 1
            );
        }
        updateButtonState(button, true);
    }
    
    try {
        const response = await fetch(`/like/${postId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: `is_like=${isLike !== null ? isLike : ''}`
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Only update if the server response is different from our optimistic update
            if (data.like_count != currentLikeCount || data.dislike_count != currentDislikeCount) {
                updatePostUI(postId, data);
            }
            
            // Show feedback message
            if (data.user_vote === null) {
                showToast('Your vote has been removed', 'info');
            } else {
                const action = data.user_vote ? 'liked' : 'disliked';
                showToast(`Post ${action} successfully!`, 'success');
            }
        } else {
            showToast(data.error || 'An error occurred', 'danger');
            // Revert optimistic update on error
            setTimeout(() => window.location.reload(), 1000);
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to process your vote. Please try again.', 'danger');
        // Revert optimistic update on error
        setTimeout(() => window.location.reload(), 1000);
    } finally {
        // Re-enable buttons
        buttons.forEach(btn => { btn.disabled = false; });
    }
}

// Update the UI after a successful vote
function updatePostUI(postId, data) {
    // Update counts
    updateCounts(postId, data.like_count, data.dislike_count);
    
    // Update button states
    const buttons = document.querySelectorAll(`[data-post-id="${postId}"]`);
    buttons.forEach(button => {
        const isLike = button.classList.contains('like-btn');
        const isActive = (isLike && data.user_vote === true) || 
                        (!isLike && data.user_vote === false);
        updateButtonState(button, isActive);
    });
}

// Update the visual state of a button
function updateButtonState(button, isActive) {
    const isLike = button.classList.contains('like-btn');
    const baseClass = isLike ? 'btn-outline-success' : 'btn-outline-danger';
    const activeClass = isLike ? 'btn-success' : 'btn-danger';
    
    button.classList.remove(baseClass, activeClass);
    button.classList.add(isActive ? activeClass : baseClass);
    
    // If activating one button, deactivate the other
    if (isActive) {
        const otherButton = button.parentElement.querySelector(isLike ? '.dislike-btn' : '.like-btn');
        if (otherButton) {
            otherButton.classList.remove('btn-danger', 'btn-success');
            otherButton.classList.add(isLike ? 'btn-outline-danger' : 'btn-outline-success');
        }
    }
}

// Update like/dislike counts
function updateCounts(postId, likeCount, dislikeCount) {
    const updateCount = (selector, count) => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            const counter = el.querySelector('.like-count, .dislike-count');
            if (counter) counter.textContent = count;
        });
    };
    
    updateCount(`.like-btn[data-post-id="${postId}"]`, likeCount);
    updateCount(`.dislike-btn[data-post-id="${postId}"]`, dislikeCount);
}

// Get CSRF token from cookies or form input
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.cookie.match(/csrftoken=([^;]+)/)?.[1] ||
           ''; // Return empty string if token not found
}

// Show toast notification
function showToast(message, type = 'info') {
    // Check if toast container exists, if not create one
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
    
    // Add click handler to close button
    const closeButton = toast.querySelector('[data-bs-dismiss="toast"]');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
    }
}
