// auth.js - Client-side authentication helpers

document.addEventListener('DOMContentLoaded', function() {
    // Handle login form submission
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const emailField = document.getElementById('email');
            const passwordField = document.getElementById('password');
            let isValid = true;
            
            // Simple email validation
            if (!emailField.value || !emailField.value.includes('@')) {
                isValid = false;
                showFormError(emailField, 'Please enter a valid email address');
            } else {
                hideFormError(emailField);
            }
            
            // Password validation
            if (!passwordField.value || passwordField.value.length < 6) {
                isValid = false;
                showFormError(passwordField, 'Password must be at least 6 characters');
            } else {
                hideFormError(passwordField);
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }
    
    // Function to show form error
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
        
        // Insert error message after input
        inputElement.parentNode.appendChild(errorElement);
    }
    
    // Function to hide form error
    function hideFormError(inputElement) {
        // Remove error styles
        inputElement.style.borderColor = '';
        
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
});