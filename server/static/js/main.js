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
    
    // Colors for different emotions
    const emotionColors = {
        'happy': '#4CAF50',
        'sad': '#2196F3',
        'angry': '#F44336',
        'surprised': '#FF9800',
        'fear': '#9C27B0',
        'disgust': '#795548',
        'neutral': '#607D8B',
        'contempt': '#FF5722'
    };
    
    // Fetch emotion statistics from the server
    function fetchEmotionStats() {
        loadingStats.style.display = 'block';
        statsContent.style.display = 'none';
        errorMessage.style.display = 'none';
        
        fetch('/api/emotion_stats')
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
                <div class="emotion-label">${emotion}</div>
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
    
    // Event listeners
    refreshButton.addEventListener('click', fetchEmotionStats);
    
    // Initial fetch
    fetchEmotionStats();
    
    // Refresh data every 30 seconds
    setInterval(fetchEmotionStats, 30000);
}); 