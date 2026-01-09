"""
Pipeline Orchestrator
Coordinates the complete podcast script generation workflow
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .api_clients import GeminiClient, DeepSeekClient
from .text_analyzer import TextAnalyzer
from .script_generator import ScriptGenerator

log = logging.getLogger(__name__)


class PodcastPipeline:
    """Main pipeline for podcast script generation"""
    
    def __init__(self, google_api_key: str, deepseek_api_key: str, 
                 output_dir: Path = Path("outputs")):
        """Initialize pipeline with API clients"""
        self.gemini = GeminiClient(google_api_key)
        self.deepseek = DeepSeekClient(deepseek_api_key)
        self.analyzer = TextAnalyzer(self.gemini, self.deepseek)
        self.generator = ScriptGenerator(self.deepseek)
        self.output_dir = output_dir
        
        # Ensure output directories exist
        (self.output_dir / "json").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "scripts").mkdir(parents=True, exist_ok=True)
        
        log.info("Pipeline initialized successfully")
    
    def generate(self,
                source: str,
                podcast_name: str = "My Podcast",
                host_name: str = "Host",
                max_chapters: int = 20,  # Changed from max_concepts
                skip_elaborate: bool = False,
                skip_polish: bool = False,
                save_intermediate: bool = True) -> Dict[str, Any]:
        """
        Run complete pipeline from book source to final script

        Args:
            source: File path, URL, or text content
            podcast_name: Name of the podcast
            host_name: Name of the host
            max_chapters: Maximum number of chapters to analyze (changed from max_concepts)
            skip_elaborate: Skip elaboration step
            skip_polish: Skip polishing step
            save_intermediate: Save analysis JSON

        Returns:
            Dictionary with script and metadata
        """
        log.info(f"Starting pipeline for: {source[:100]}...")
        start_time = datetime.now()

        try:
            # Step 1: Analyze content
            log.info("Step 1/2: Analyzing book content...")
            analysis = self.analyzer.process(source, max_chapters)

            if not analysis:
                return {
                    "success": False,
                    "error": "Content analysis failed"
                }

            # Save analysis if requested
            if save_intermediate:
                analysis_file = self.output_dir / "json" / f"analysis_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
                analysis_file.write_text(json.dumps(analysis, indent=2))
                log.info(f"Analysis saved to: {analysis_file}")

            # Step 2: Generate script
            log.info("Step 2/2: Generating script...")
            script = self.generator.generate_complete(
                analysis,
                podcast_name,
                host_name,
                skip_elaborate,
                skip_polish
            )

            if not script:
                return {
                    "success": False,
                    "error": "Script generation failed"
                }

            # Save script
            script_file = self.output_dir / "scripts" / f"script_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
            script_file.write_text(script)
            log.info(f"Script saved to: {script_file}")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "script": script,
                "script_file": str(script_file),
                "analysis_file": str(analysis_file) if save_intermediate else None,
                "metadata": {
                    "source": source[:200],
                    "podcast_name": podcast_name,
                    "host_name": host_name,
                    "duration_seconds": duration,
                    "script_length": len(script),
                    "word_count": len(script.split()),
                    "num_chapters": len(analysis.get("ideas", [])),  # Changed to ideas
                    "timestamp": start_time.isoformat()
                }
            }

            log.info(f"Pipeline completed in {duration:.1f} seconds")
            return result

        except Exception as e:
            log.error(f"Pipeline error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
