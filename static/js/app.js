// Podcast Script Generator - Frontend JavaScript

let currentScriptData = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('scriptForm');
    form.addEventListener('submit', handleSubmit);
    
    // Check API health
    checkHealth();
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

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();
    
    // Get form data
    const formData = {
        source: document.getElementById('source').value.trim(),
        podcast_name: document.getElementById('podcast_name').value.trim(),
        host_name: document.getElementById('host_name').value.trim(),
        max_concepts: parseInt(document.getElementById('max_concepts').value),
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
    
    // Show progress
    showProgress();
    
    // Disable form
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.querySelector('.btn-text').textContent = 'Generating...';
    generateBtn.querySelector('.spinner').style.display = 'inline-block';
    
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
        // Re-enable form
        generateBtn.disabled = false;
        generateBtn.querySelector('.btn-text').textContent = 'Generate Script';
        generateBtn.querySelector('.spinner').style.display = 'none';
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
    document.getElementById('wordCount').textContent = `📝 ${metadata.word_count} words`;
    document.getElementById('duration').textContent = `⏱️ ${Math.round(metadata.duration_seconds)}s generation`;
    document.getElementById('concepts').textContent = `💡 ${metadata.num_concepts} concepts`;
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Copy script to clipboard
async function copyScript() {
    if (!currentScriptData) return;
    
    try {
        await navigator.clipboard.writeText(currentScriptData.script);
        
        // Visual feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
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
