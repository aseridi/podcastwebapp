"""
Flask Web Application for Podcast Script Generator
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime

from config.config import API_KEYS, PIPELINE_CONFIG, OUTPUT_DIR, LOGS_DIR
from app.core.pipeline import PodcastPipeline

# Setup logging
log_file = LOGS_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
CORS(app)

# Initialize pipeline
try:
    pipeline = PodcastPipeline(
        google_api_key=API_KEYS["google"],
        deepseek_api_key=API_KEYS["deepseek"],
        output_dir=OUTPUT_DIR
    )
    log.info("Pipeline initialized successfully")
except Exception as e:
    log.error(f"Failed to initialize pipeline: {e}")
    pipeline = None


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate_script():
    """Generate podcast script endpoint"""
    if not pipeline:
        return jsonify({
            "success": False,
            "error": "Pipeline not initialized. Check API keys."
        }), 500
    
    try:
        data = request.get_json()
        
        # Validate input
        source = data.get('source', '').strip()
        if not source:
            return jsonify({
                "success": False,
                "error": "Source content is required"
            }), 400
        
        # Get optional parameters
        podcast_name = data.get('podcast_name', 'My Podcast').strip()
        host_name = data.get('host_name', 'Your Name').strip()
        max_concepts = int(data.get('max_concepts', PIPELINE_CONFIG['max_concepts']))
        skip_elaborate = data.get('skip_elaborate', False)
        skip_polish = data.get('skip_polish', False)
        
        log.info(f"Generating script for: {source[:100]}...")
        
        # Run pipeline
        result = pipeline.generate(
            source=source,
            podcast_name=podcast_name,
            host_name=host_name,
            max_concepts=max_concepts,
            skip_elaborate=skip_elaborate,
            skip_polish=skip_polish,
            save_intermediate=True
        )
        
        return jsonify(result)
    
    except Exception as e:
        log.error(f"Error in generate endpoint: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download generated script"""
    try:
        file_path = OUTPUT_DIR / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name
        )
    except Exception as e:
        log.error(f"Error downloading file: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "api_keys_configured": all(API_KEYS.values())
    })


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
