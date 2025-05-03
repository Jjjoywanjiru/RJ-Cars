// Enhanced auth.js - Client-side authentication helpers

document.addEventListener('DOMContentLoaded', function() {
    // Handle login form submission
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        // Add input event listeners for real-time validation
        const emailField = document.getElementById('email');
        const passwordField = document.getElementById('password');
        
        if (emailField) {
            emailField.addEventListener('input', function() {
                validateEmail(emailField);
            });
        }
        
        if (passwordField) {
            passwordField.addEventListener('input', function() {
                validatePassword(passwordField);
            });
        }
        
        loginForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Email validation
            if (!validateEmail(emailField)) {
                isValid = false;
            }
            
            // Password validation
            if (!validatePassword(passwordField)) {
                isValid = false;
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Function to validate email
    function validateEmail(inputElement) {
        if (!inputElement) return true;
        
        if (!inputElement.value) {
            showFormError(inputElement, 'Email is required');
            return false;
        } else if (!isValidEmail(inputElement.value)) {
            showFormError(inputElement, 'Please enter a valid email address');
            return false;
        } else {
            hideFormError(inputElement);
            return true;
        }
    }
    
    // Function to validate password
    function validatePassword(inputElement) {
        if (!inputElement) return true;
        
        if (!inputElement.value) {
            showFormError(inputElement, 'Password is required');
            return false;
        } else if (inputElement.value.length < 6) {
            showFormError(inputElement, 'Password must be at least 6 characters');
            return false;
        } else {
            hideFormError(inputElement);
            return true;
        }
    }
    
    // Email regex validation
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Function to show form error with improved styling
    function showFormError(inputElement, message) {
        // Remove any existing error message
        hideFormError(inputElement);
        
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'form-error';
        errorElement.textContent = message;
        errorElement.style.color = '#721c24';
        errorElement.style.fontSize = '0.85rem';
        errorElement.style.marginTop = '5px';
        
        // Add error styles to input
        inputElement.style.borderColor = '#f5c6cb';
        inputElement.classList.add('input-error');
        
        // Insert error message after input
        inputElement.parentNode.appendChild(errorElement);
    }
    
    // Function to hide form error
    function hideFormError(inputElement) {
        // Remove error styles
        inputElement.style.borderColor = '';
        inputElement.classList.remove('input-error');
        
        // Remove error message if exists
        const errorElement = inputElement.parentNode.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    // Automatically hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s ease';
                
                setTimeout(function() {
                    message.style.display = 'none';
                }, 500);
            });
        }, 5000);
    }
    
    // Add event listeners to check session status for protected routes
    const protectedLinks = document.querySelectorAll('a[data-protected="true"]');
    if (protectedLinks) {
        protectedLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                // Check if user is logged in via session cookie presence
                // This is a simple check and should be supplemented with server-side validation
                if (!document.cookie.includes('session=')) {
                    e.preventDefault();
                    showLoginPrompt(link.getAttribute('href'));
                }
            });
        });
    }
    
    // Function to show login prompt
    function showLoginPrompt(targetUrl) {
        // Store the target URL in local storage
        if (targetUrl) {
            sessionStorage.setItem('redirectAfterLogin', targetUrl);
        }
        
        // Create a modal or redirect to login
        window.location.href = '/login';
    }
});