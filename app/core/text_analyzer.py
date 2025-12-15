"""
Text Analysis and Structuring
Analyzes input text and extracts themes, concepts, and structure
"""

import logging
import re
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import trafilatura
from typing import Optional, Dict, Any, List
from .api_clients import GeminiClient, DeepSeekClient

log = logging.getLogger(__name__)


class TextAnalyzer:
    """Analyzes text content and structures it for script generation"""
    
    def __init__(self, gemini_client: GeminiClient, deepseek_client: DeepSeekClient):
        self.gemini = gemini_client
        self.deepseek = deepseek_client
    
    def load_content(self, source: str) -> Optional[str]:
        """Load content from file, URL, or direct text"""
    # Check if it's a URL
        if source.startswith(('http://', 'https://')):
            return self._fetch_url(source)
        
        # Check if it's a file path
        if len(source) <= 260 and '\n' not in source:
            try:
                path = Path(source)
                if path.exists() and path.is_file():
                    return self._read_file(path)
            except OSError:
                # Path too long or invalid - treat as direct text
                pass
        
        # Treat as direct text
        return source.strip() if source.strip() else None
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch and extract clean article text using Trafilatura."""
        try:
            # download() handles headers, user-agents, and timeouts automatically
            downloaded = trafilatura.fetch_url(url)
            
            if downloaded is None:
                log.warning(f"Empty response from {url}")
                return None

            # extract() uses heuristics to find the main content
            text = trafilatura.extract(
                downloaded, 
                include_comments=False, 
                include_tables=False, 
                no_fallback=False
            )
            
            return text
        except Exception as e:
            log.error(f"Failed to fetch/parse URL {url}: {e}")
            return None
    
    def _read_file(self, path: Path) -> Optional[str]:
        """Read text file with encoding detection"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        
        log.error(f"Failed to read file {path} with any encoding")
        return None
    
    def chunk_text(self, text: str, chunk_size: int = 2000, 
                   min_size: int = 500) -> List[str]:
        """Split text into manageable chunks"""
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_len = len(para)
            
            if current_length + para_len > chunk_size and current_length > min_size:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_len
            else:
                current_chunk.append(para)
                current_length += para_len
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        log.info(f"Text split into {len(chunks)} chunks")
        return chunks
    
    def analyze_themes(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract main themes and topics from text"""
        prompt = f"""Analyze this text and identify:
1. Main theme (one sentence describing the core topic and what aspects it covers)
2. Key concepts (5-10 important ideas)
3. Overall tone and style
4. Target audience insights

Text:
{text[:5000]}

Respond with a JSON object containing: theme (string), concepts (list), tone (string), audience (string)."""

        response = self.gemini.generate(prompt)
        if not response:
            return None
        
        # Parse JSON from response
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find raw JSON
            first_brace = response.find('{')
            last_brace = response.rfind('}')
            if first_brace != -1 and last_brace != -1:
                return json.loads(response[first_brace:last_brace + 1])
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON from analysis: {e}")
        
        return None
    
    def analyze_concepts(self, text: str, max_concepts: int = 12) -> List[Dict[str, str]]:
        """Deep analysis of key concepts"""
        prompt = f"""Identify and explain the {max_concepts} most important concepts from this text.
For each concept provide:
- name: Short name
- description: 2-3 sentence explanation
- importance: Why it matters

Text:
{text[:8000]}

Respond with a JSON array of concept objects."""

        response = self.deepseek.generate(prompt, temperature=0.7)
        if not response:
            return []
        
        try:
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            first_bracket = response.find('[')
            last_bracket = response.rfind(']')
            if first_bracket != -1 and last_bracket != -1:
                return json.loads(response[first_bracket:last_bracket + 1])
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse concepts JSON: {e}")
        
        return []

    def create_outline(self, text: str, themes: Dict[str, Any], 
                       concepts: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """Create detailed outline for content structure"""
        log.info("Creating content outline...")
        
        theme = themes.get("theme", "")
        concept_names = [c.get("name", "") for c in concepts[:10]]
        
        prompt = f"""Based on this content analysis, create a detailed outline for a podcast episode.

MAIN THEME: {theme}
KEY CONCEPTS: {", ".join(concept_names)}

CONTENT PREVIEW:
{text[:6000]}

Create an outline with 5-8 sections. For each section provide:
- section_number: Number (1, 2, 3...)
- title: Short section title
- focus: What this section covers (2-3 sentences)
- key_points: List of 3-5 specific points to discuss
- relevant_concepts: Which concepts from the list are relevant here

Structure should flow logically from introduction to conclusion.

Respond with a JSON array of section objects."""

        response = self.gemini.generate(prompt, temperature=0.7)
        if not response:
            return None
        
        # Parse JSON array
        try:
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            first_bracket = response.find('[')
            last_bracket = response.rfind(']')
            if first_bracket != -1 and last_bracket != -1:
                return json.loads(response[first_bracket:last_bracket + 1])
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse outline JSON: {e}")
        
        return None
    
    def process(self, source: str, max_concepts: int = 12) -> Optional[Dict[str, Any]]:
        """Complete analysis pipeline"""
        log.info("Starting text analysis...")
        
        # Load content
        text = self.load_content(source)
        if not text:
            log.error("Failed to load content")
            return None
        
        log.info(f"Loaded text: {len(text)} characters")
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Analyze themes
        themes = self.analyze_themes(text)
        
        # Analyze concepts
        concepts = self.analyze_concepts(text, max_concepts)

        # Create outline
        outline = self.create_outline(text, themes or {}, concepts)
        
        result = {
            "source": source,
            "themes": themes or {},
            "concepts": concepts,
            "chunks": chunks,
            "outline": outline or [],
            "full_text": text,
            "metadata": {
                "total_length": len(text),
                "num_chunks": len(chunks),
                "num_concepts": len(concepts),
                "num_sections": len(outline) if outline else 0
            }
        }
        
        log.info("Analysis complete")
        return result