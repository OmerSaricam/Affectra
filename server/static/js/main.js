document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const loadingStats = document.getElementById('loading-stats');
    const statsContent = document.getElementById('stats-content');
    const errorMessage = document.getElementById('error-message');
    const dominantEmotion = document.getElementById('dominant-emotion');
    const avgDuration = document.getElementById('avg-duration');
    const emotionPercentages = document.getElementById('emotion-percentages');
    const lastUpdate = document.getElementById('last-update');
    const refreshButton = document.getElementById('refresh-stats');
    const clearButton = document.getElementById('clear-data');
    const confirmClearButton = document.getElementById('confirm-clear');
    const clearStatus = document.getElementById('clear-status');
    const visitorCount = document.getElementById('visitor-count');
    const emptyDataMessage = document.getElementById('empty-data-message');
    
    // Bootstrap modal
    const confirmModal = new bootstrap.Modal(document.getElementById('confirmModal'));
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    
    // Colors for different emotions - use distinct colors for each emotion
    const emotionColors = {
        'happy': '#4CAF50',    // Green
        'sad': '#2196F3',      // Blue
        'angry': '#F44336',    // Red
        'surprised': '#FF9800', // Orange
        'fear': '#9C27B0',     // Purple
        'disgust': '#795548',  // Brown
        'neutral': '#607D8B',  // Gray-Blue
        'contempt': '#FF5722'  // Deep Orange
    };
    
    // Secure fetch function that adds CSRF token and other security headers
    function secureFetch(url, options = {}) {
        const defaultOptions = {
            credentials: 'same-origin', // Include cookies
            cache: 'no-cache', // Don't cache requests
            headers: {
                'X-CSRF-Token': csrfToken,
                'Content-Type': 'application/json'
            }
        };
        
        // Merge the default options with any provided options
        const mergedOptions = { 
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...(options.headers || {})
            }
        };
        
        return fetch(url, mergedOptions);
    }
    
    // Fetch emotion statistics from the server
    function fetchEmotionStats() {
        loadingStats.style.display = 'block';
        statsContent.style.display = 'none';
        errorMessage.style.display = 'none';
        emptyDataMessage.style.display = 'none';
        
        secureFetch('/api/emotion_stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch statistics');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'ok') {
                    updateStats(data);
                    loadingStats.style.display = 'none';
                    statsContent.style.display = 'block';
                    
                    // Show empty data message if needed
                    emptyDataMessage.style.display = data.is_empty ? 'block' : 'none';
                    
                    // Update last fetch time
                    const now = new Date();
                    lastUpdate.textContent = `Last updated: ${now.toLocaleTimeString()}`;
                } else {
                    throw new Error(data.message || 'Unknown error');
                }
            })
            .catch(error => {
                console.error('Error fetching statistics:', error);
                loadingStats.style.display = 'none';
                errorMessage.style.display = 'block';
                errorMessage.textContent = error.message || 'Failed to load statistics. Please try again later.';
            });
    }
    
    // Update the UI with the fetched statistics
    function updateStats(data) {
        // Update visitor count
        visitorCount.textContent = data.visitor_count;
        
        // Check if data is empty
        if (data.is_empty) {
            // Show custom message for empty data
            dominantEmotion.textContent = "No data";
            dominantEmotion.style.color = "#777";
            
            avgDuration.textContent = "0";
            
            // Show empty state for emotion percentages
            emotionPercentages.innerHTML = '<div class="alert alert-secondary">No emotion data available. Start tracking to see statistics.</div>';
            return;
        }
        
        // Update dominant emotion
        dominantEmotion.textContent = data.overall_dominant_emotion;
        dominantEmotion.style.color = emotionColors[data.overall_dominant_emotion] || '#333';
        
        // Update average duration
        avgDuration.textContent = data.avg_duration;
        
        // Update emotion percentages
        emotionPercentages.innerHTML = '';
        
        // Sort emotions by percentage (descending)
        const sortedEmotions = Object.entries(data.avg_emotion_percentages)
            .sort((a, b) => b[1] - a[1]);
        
        sortedEmotions.forEach(([emotion, percentage]) => {
            const roundedPercentage = Math.round(percentage * 10) / 10;
            const color = emotionColors[emotion] || '#333';
            
            const emotionDiv = document.createElement('div');
            emotionDiv.className = 'emotion-row';
            emotionDiv.innerHTML = `
                <div class="emotion-label">${sanitizeHtml(emotion)}</div>
                <div class="progress">
                    <div class="progress-bar" 
                         role="progressbar" 
                         style="width: ${roundedPercentage}%; background-color: ${color};" 
                         aria-valuenow="${roundedPercentage}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${roundedPercentage}%
                    </div>
                </div>
            `;
            
            emotionPercentages.appendChild(emotionDiv);
        });
    }
    
    // Simple HTML sanitizer for security
    function sanitizeHtml(text) {
        const element = document.createElement('div');
        element.textContent = text;
        return element.innerHTML;
    }
    
    // Clear all emotion data
    function clearData() {
        secureFetch('/api/clear_data', {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to clear data: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'ok') {
                // Show success message
                clearStatus.innerHTML = '<div class="alert alert-success">All tracking data has been cleared. New statistics will appear when new sessions are recorded.</div>';
                clearStatus.style.display = 'block';
                
                // Refresh statistics to show updated data
                fetchEmotionStats();
                
                // Hide success message after 5 seconds
                setTimeout(() => {
                    clearStatus.style.display = 'none';
                }, 5000);
            } else {
                throw new Error(data.message || 'Failed to clear data');
            }
        })
        .catch(error => {
            console.error('Error clearing data:', error);
            clearStatus.innerHTML = `<div class="alert alert-danger">Error: ${sanitizeHtml(error.message)}</div>`;
            clearStatus.style.display = 'block';
        });
    }
    
    // Event listeners
    refreshButton.addEventListener('click', fetchEmotionStats);
    
    clearButton.addEventListener('click', function() {
        confirmModal.show();
    });
    
    confirmClearButton.addEventListener('click', function() {
        confirmModal.hide();
        clearData();
    });
    
    // Initial fetch
    fetchEmotionStats();
    
    // Refresh data every 30 seconds
    setInterval(fetchEmotionStats, 30000);
}); 