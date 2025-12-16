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
from app.core.tts_generator import TTSGenerator

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

# Initialize TTS Generator
try:
    tts_generator = TTSGenerator(api_key=API_KEYS["google_tts"])
    log.info("TTS Generator initialized successfully")
except Exception as e:
    log.error(f"Failed to initialize TTS: {e}")
    tts_generator = None


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

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from script text"""
    if not tts_generator:
        return jsonify({
            "success": False,
            "error": "TTS not initialized. Check Google API key."
        }), 500
    
    try:
        data = request.get_json()
        
        # Get script text
        script = data.get('script', '').strip()
        if not script:
            return jsonify({
                "success": False,
                "error": "Script text is required"
            }), 400
        
        # Optional parameters
        voice = data.get('voice', 'Schedar')
        temperature = float(data.get('temperature', 1.0))
        
        # Ensure output directory exists
        audio_output_dir = OUTPUT_DIR / "audio"
        audio_output_dir.mkdir(parents=True, exist_ok=True)
        
        log.info(f"Generating audio for script ({len(script)} chars)...")
        
        # Generate audio
        audio_path = tts_generator.generate_audio(
            text=script,
            output_path=audio_output_dir,
            voice=voice,
            temperature=temperature
        )
        
        if not audio_path:
            return jsonify({
                "success": False,
                "error": "Audio generation failed"
            }), 500
        
        return jsonify({
            "success": True,
            "audio_file": str(audio_path),
            "filename": audio_path.name,
            "download_url": f"/api/download/audio/{audio_path.name}"
        })
        
    except Exception as e:
        log.error(f"Error in generate-audio endpoint: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

@app.route('/api/download/audio/<filename>')
def download_audio(filename):
    """Download generated audio file"""
    try:
        file_path = OUTPUT_DIR / "audio" / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/wav'
        )
    except Exception as e:
        log.error(f"Error downloading audio: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts/voices')
def get_voices():
    """Get available TTS voices"""
    if not tts_generator:
        return jsonify({"voices": []})
    
    return jsonify({"voices": TTSGenerator.VOICES})

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
