// Podcast Script Generator - Frontend JavaScript

let currentScriptData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check API health
    checkHealth();
    
    // Load available TTS voices
    loadVoices();
});

// Check API health
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (!data.pipeline_ready || !data.api_keys_configured) {
            showError('API not properly configured. Please check your API keys.');
        }
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

// Load available voices
async function loadVoices() {
    try {
        const response = await fetch('/api/tts/voices');
        const data = await response.json();
        
        const voiceSelect = document.getElementById('voiceSelect');
        if (voiceSelect && data.voices && data.voices.length > 0) {
            voiceSelect.innerHTML = data.voices
                .map(v => `<option value="${v}" ${v === 'Schedar' ? 'selected' : ''}>${v}</option>`)
                .join('');
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
    }
}

// Handle script generation
async function handleGenerateScript() {
    // Get form data
    const formData = {
        source: document.getElementById('source').value.trim(),
        podcast_name: document.getElementById('podcast_name').value.trim(),
        host_name: document.getElementById('host_name').value.trim(),
        max_chapters: parseInt(document.getElementById('max_chapters').value),
        skip_elaborate: document.getElementById('skip_elaborate').checked,
        skip_polish: document.getElementById('skip_polish').checked
    };
    
    // Validate
    if (!formData.source) {
        showError('Please enter content to analyze');
        return;
    }
    
    // Hide previous results/errors
    hideError();
    document.getElementById('resultsSection').style.display = 'none';
    
    // Hide audio player if it exists
    const audioPlayerContainer = document.getElementById('audioPlayerContainer');
    if (audioPlayerContainer) {
        audioPlayerContainer.style.display = 'none';
    }
    
    // Show progress
    showProgress();
    
    // Disable both buttons
    const scriptBtn = document.getElementById('scriptBtn');
    const audioBtn = document.getElementById('audioBtn');
    scriptBtn.disabled = true;
    audioBtn.disabled = true;
    scriptBtn.querySelector('.btn-text').textContent = 'Generating...';
    scriptBtn.querySelector('.spinner').style.display = 'inline-block';
    
    try {
        // Simulate progress updates
        updateProgress(10, 'Analyzing content...');
        
        // Call API
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        updateProgress(50, 'Generating draft script...');
        
        const result = await response.json();
        
        updateProgress(90, 'Finalizing...');
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Generation failed');
        }
        
        // Success!
        updateProgress(100, 'Complete!');
        setTimeout(() => {
            showResults(result);
        }, 500);
        
    } catch (error) {
        console.error('Generation error:', error);
        showError(error.message || 'Failed to generate script. Please try again.');
        document.getElementById('progressSection').style.display = 'none';
    } finally {
        // Re-enable both buttons
        scriptBtn.disabled = false;
        audioBtn.disabled = false;
        scriptBtn.querySelector('.btn-text').textContent = 'Generate Script';
        scriptBtn.querySelector('.spinner').style.display = 'none';
    }
}

// Handle audio-only generation (no script needed)
async function handleGenerateAudio() {
    // Get text from source field
    const sourceText = document.getElementById('source').value.trim();
    
    // Validate
    if (!sourceText) {
        showError('Please enter text to convert to audio');
        return;
    }
    
    // Hide errors
    hideError();
    
    // Get selected voice
    const voiceSelect = document.getElementById('voiceSelect');
    const voice = voiceSelect ? voiceSelect.value : 'Schedar';
    
    // Disable both buttons
    const scriptBtn = document.getElementById('scriptBtn');
    const audioBtn = document.getElementById('audioBtn');
    const originalText = audioBtn.textContent;
    
    scriptBtn.disabled = true;
    audioBtn.disabled = true;
    audioBtn.textContent = '🔊 Generating Audio...';
    
    try {
        const response = await fetch('/api/generate-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                script: sourceText,
                voice: voice,
                temperature: 1.0
            })
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Audio generation failed');
        }
        
        // Show audio player
        showAudioPlayer(result.download_url, result.filename);
        
        // Visual feedback
        audioBtn.textContent = '✅ Audio Ready!';
        audioBtn.style.background = '#10b981';
        
        setTimeout(() => {
            audioBtn.textContent = originalText;
            audioBtn.style.background = '';
        }, 3000);
        
    } catch (error) {
        console.error('Audio generation error:', error);
        showError(error.message || 'Failed to generate audio');
        audioBtn.textContent = originalText;
    } finally {
        // Re-enable both buttons
        scriptBtn.disabled = false;
        audioBtn.disabled = false;
    }
}

// Show progress
function showProgress() {
    document.getElementById('progressSection').style.display = 'block';
    updateProgress(0, 'Starting...');
}

// Update progress
function updateProgress(percent, message) {
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressText').textContent = message;
}

// Show results
function showResults(result) {
    currentScriptData = result;
    
    // Hide progress
    document.getElementById('progressSection').style.display = 'none';
    
    // Show results section
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    
    // Populate script
    document.getElementById('scriptOutput').textContent = result.script;
    
    // Populate metadata
    const metadata = result.metadata;
    document.getElementById('wordCount').textContent = `${metadata.word_count} words`;
    document.getElementById('duration').textContent = `${Math.round(metadata.duration_seconds)}s generation`;
    document.getElementById('concepts').textContent = `${metadata.num_chapters} chapters`;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Generate audio from existing script (called from results section)
async function generateAudioFromScript() {
    if (!currentScriptData || !currentScriptData.script) {
        showError('No script available. Generate a script first.');
        return;
    }
    
    const audioBtn = document.getElementById('audioFromScriptBtn');
    const originalText = audioBtn.textContent;
    
    // Get selected voice
    const voiceSelect = document.getElementById('voiceSelect');
    const voice = voiceSelect ? voiceSelect.value : 'Schedar';
    
    try {
        // Update button state
        audioBtn.disabled = true;
        audioBtn.textContent = '🔊 Generating Audio...';
        
        const response = await fetch('/api/generate-audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                script: currentScriptData.script,
                voice: voice,
                temperature: 1.0
            })
        });
        
        const result = await response.json();
        
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Audio generation failed');
        }
        
        // Show audio player
        showAudioPlayer(result.download_url, result.filename);
        
        // Visual feedback
        audioBtn.textContent = 'Audio Ready!';
        audioBtn.style.background = '#10b981';
        
        setTimeout(() => {
            audioBtn.textContent = originalText;
            audioBtn.style.background = '';
            audioBtn.disabled = false;
        }, 3000);
        
    } catch (error) {
        console.error('Audio generation error:', error);
        showError(error.message || 'Failed to generate audio');
        audioBtn.textContent = originalText;
        audioBtn.disabled = false;
    }
}

// Show audio player
function showAudioPlayer(url, filename) {
    // Check if player already exists
    let playerContainer = document.getElementById('audioPlayerContainer');
    
    if (!playerContainer) {
        // Create player container
        playerContainer = document.createElement('div');
        playerContainer.id = 'audioPlayerContainer';
        playerContainer.className = 'audio-player-container';
        playerContainer.innerHTML = `
            <h4>🎧 Generated Audio</h4>
            <audio id="audioPlayer" controls style="width: 100%; margin: 1rem 0;"></audio>
            <div class="audio-actions">
                <a id="audioDownloadLink" class="btn-secondary" download>Download Audio</a>
            </div>
        `;
        
        // Insert after form card or at top of results
        const mainCard = document.querySelector('.card');
        if (mainCard && mainCard.nextSibling) {
            mainCard.parentNode.insertBefore(playerContainer, mainCard.nextSibling);
        }
    }
    
    // Update player source
    const audioPlayer = document.getElementById('audioPlayer');
    const downloadLink = document.getElementById('audioDownloadLink');
    
    audioPlayer.src = url;
    downloadLink.href = url;
    downloadLink.download = filename;
    
    playerContainer.style.display = 'block';
    
    // Scroll to player
    playerContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Copy script to clipboard
async function copyScript() {
    if (!currentScriptData) return;
    
    try {
        await navigator.clipboard.writeText(currentScriptData.script);
        
        // Visual feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = 'Copied!';
        btn.style.background = '#10b981';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    } catch (error) {
        showError('Failed to copy to clipboard');
    }
}

// Download script
function downloadScript() {
    if (!currentScriptData) return;
    
    const scriptText = currentScriptData.script;
    const metadata = currentScriptData.metadata;
    const filename = `podcast_script_${metadata.timestamp.split('T')[0]}.txt`;
    
    // Create blob and download
    const blob = new Blob([scriptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Show error
function showError(message) {
    const errorSection = document.getElementById('errorSection');
    document.getElementById('errorMessage').textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide error
function hideError() {
    document.getElementById('errorSection').style.display = 'none';
}