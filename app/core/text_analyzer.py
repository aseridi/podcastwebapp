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
    
    def chunk_text(self, text: str, chunk_size: int = 3000,
                   min_size: int = 1000) -> List[str]:
        """Split book text into manageable chunks, preserving chapter boundaries when possible"""

        # Try to split by chapter markers first
        chapter_patterns = [
            r'\n\s*Chapter\s+\d+',
            r'\n\s*CHAPTER\s+[IVXLCDM]+',
            r'\n\s*Part\s+\d+',
            r'\n\s*Section\s+\d+',
            r'\n\s*\d+\.\s*[A-Z]',  # Numbered sections
        ]

        chunks = []

        # Try chapter-based splitting first
        for pattern in chapter_patterns:
            parts = re.split(pattern, text)
            if len(parts) > 1:
                log.info(f"Found {len(parts)} chapters/sections using pattern: {pattern}")
                # Each chapter becomes a chunk (or multiple if very long)
                for part in parts:
                    if len(part.strip()) > min_size:
                        if len(part) > chunk_size:
                            # Chapter is too long, sub-divide by paragraphs
                            sub_chunks = self._chunk_by_paragraphs(part, chunk_size, min_size)
                            chunks.extend(sub_chunks)
                        else:
                            chunks.append(part.strip())

                if chunks:
                    log.info(f"Text split into {len(chunks)} chapter-aware chunks")
                    return chunks

        # Fallback to paragraph-based chunking
        log.info("No clear chapter structure found, using paragraph-based chunking")
        return self._chunk_by_paragraphs(text, chunk_size, min_size)

    def _chunk_by_paragraphs(self, text: str, chunk_size: int, min_size: int) -> List[str]:
        """Helper method: chunk by paragraphs"""
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

        return chunks
    
    def analyze_themes(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract main IDEAS and philosophical themes from text"""
        prompt = f"""Analyze this book focusing on its IDEAS, THEMES, and MESSAGES (not plot summary).

Your goal: Extract the INTELLECTUAL CONTENT - what ideas is the author exploring? What questions are they asking?

Identify:

1. **Central Question/Thesis**: What is the main IDEA or question this book explores? (2-3 sentences)
   - Not "what happens" but "what does it make you think about?"
   - Example: "What does it mean to live authentically in an absurd universe?"

2. **Key Philosophical Themes** (8-15 items): The BIG IDEAS this book explores
   - Focus on concepts, not plot points
   - Examples: "The tension between freedom and responsibility", "The role of suffering in meaning-making"
   - NOT: "Chapter 3 where the character does X"

3. **Intellectual Tradition**: What philosophical or cultural conversation does this fit into?
   - Examples: "Existentialism", "Absurdism", "Critique of capitalism", "Buddhist philosophy"

4. **Author's Approach**: How does the author EXPLORE these ideas?
   - Through narrative? Through argument? Through metaphor?

5. **Core Message**: What is the author ultimately trying to communicate about how to live/think/see the world?

Book text (opening section):
{text[:8000]}

Respond with JSON containing:
- central_question (string): The main intellectual question/thesis
- themes (list of strings): 8-15 philosophical themes/ideas (NOT plot points)
- tradition (string): What intellectual tradition this belongs to
- approach (string): How the author explores these ideas
- core_message (string): The ultimate takeaway about life/reality/existence

Example response:
{{
  "central_question": "How can we live authentically and find meaning in a universe that is fundamentally absurd and indifferent to human desires?",
  "themes": [
    "The tension between our desire for meaning and the meaninglessness of the universe",
    "Rebellion as a response to absurdity",
    "The danger of philosophical systems that escape reality",
    "Lucidity vs. happiness as life goals",
    "The role of physical embodiment and presence"
  ],
  "tradition": "Absurdism, Existentialism, Mediterranean philosophy",
  "approach": "Through narrative fiction that embodies philosophical ideas in characters and situations",
  "core_message": "True freedom comes from facing the absurd without escaping into false meaning, and revolting against it through authentic engagement with life"
}}
"""

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
    
    def analyze_ideas(self, text: str, max_ideas: int = 15) -> List[Dict[str, str]]:
        """Deep analysis of philosophical IDEAS (not plot points)"""
        prompt = f"""Identify the {max_ideas} most important PHILOSOPHICAL IDEAS and THEMES from this book.

CRITICAL: Focus on IDEAS, not plot. We want the intellectual/philosophical content.

For each idea provide:
- **name**: Concise name of the concept/theme (e.g., "The Absurd", "Revolt vs Suicide")
- **explanation**: 3-4 sentences explaining this IDEA/THEME
  * What is the concept?
  * Why does it matter?
  * How does it challenge conventional thinking?
- **how_explored**: How does the author explore this idea in the book?
  * Through which characters, situations, or arguments?
  * What makes their treatment of this idea unique or interesting?
- **implications**: What does this idea mean for how we should live or think? (2-3 sentences)

Focus on extracting the PHILOSOPHICAL/INTELLECTUAL content, not plot summary.

Examples of GOOD ideas to extract:
✅ "The tension between our need for meaning and the universe's indifference"
✅ "Happiness as harmony vs. lucidity as seeing clearly"
✅ "The dangers of philosophical abstraction as escape from reality"

Examples of BAD (too plot-focused):
❌ "Meursault kills someone on a beach"
❌ "The protagonist goes to a funeral"

Book text:
{text[:12000]}

Respond with a JSON array of idea objects.

Example format:
[
  {{
    "name": "The Absurd",
    "explanation": "The fundamental tension between humanity's desire for meaning, clarity, and order, and the universe's silence and indifference. This isn't just about meaninglessness - it's about the collision between what we need and what reality provides. The absurd is the feeling that arises when we fully recognize this gap.",
    "how_explored": "Through the character of Meursault, who embodies indifference and detachment. His inability to play society's emotional games reveals how most people escape the absurd by pretending things matter in conventional ways.",
    "implications": "We must choose how to respond: escape through false meaning, commit suicide, or revolt by living fully while acknowledging the absurd. The authentic response is revolt - continuing to care and act even though the universe doesn't care back."
  }}
]
"""

        response = self.deepseek.generate(prompt, temperature=0.7)
        if not response:
            return []

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
            log.error(f"Failed to parse chapters JSON: {e}")

        return []

    def create_outline(self, text: str, themes: Dict[str, Any],
                       ideas: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """Create outline focused on EXPLORING IDEAS, not summarizing plot"""
        log.info("Creating ideas-focused podcast outline...")

        central_question = themes.get("central_question", "")
        tradition = themes.get("tradition", "")
        theme_list = themes.get("themes", [])
        idea_names = [i.get("name", "") for i in ideas[:12]]

        prompt = f"""Create a podcast outline that EXPLORES THE IDEAS in this book, not just summarizes the plot.

GOAL: Take listeners on an intellectual journey through the book's philosophical content.

CENTRAL QUESTION: {central_question}
INTELLECTUAL TRADITION: {tradition}
KEY THEMES: {", ".join(theme_list[:10])}
IDEAS TO EXPLORE: {", ".join(idea_names)}

BOOK PREVIEW:
{text[:8000]}

Create 6-10 podcast sections that explore these ideas. Each section should:

**Focus on INTELLECTUAL CONTENT:**
- Explore a major idea/theme, not just "what happens in chapters 1-3"
- Use plot/characters as EXAMPLES to illustrate ideas
- Compare to other thinkers or everyday experiences
- Ask thought-provoking questions

**Structure like Philosophize This:**
- Start with why this idea matters
- Explain the concept clearly
- Show how the book explores it
- Discuss implications for life

For each section provide:

- **section_number**: 1, 2, 3...
- **title**: Engaging title about the IDEA (e.g., "The Mediterranean Spirit vs European Guilt" NOT "Chapters 1-3")
- **main_idea**: What philosophical concept/theme is this section about? (2-3 sentences)
- **key_points**: 5-8 specific things to explore:
  * The core concept/question
  * How the book illustrates it (with examples)
  * Contrasts with other ways of thinking
  * Real-world implications
  * Provocative questions to raise
- **approach**: How to discuss this (analytical, storytelling, compare/contrast, etc.)
- **connections**: How this idea relates to others in the book or to other thinkers

EXAMPLE SECTION (from Philosophize This on Camus):
{{
  "section_number": 3,
  "title": "Happiness vs. Lucidity: Why Meursault Isn't a Hero",
  "main_idea": "Camus uses Meursault to critique happiness as life's goal. If happiness is just willpower and framing, it becomes an escape from reality - the same philosophical suicide Camus warns against. True authenticity requires lucidity (seeing clearly) even when uncomfortable.",
  "key_points": [
    "The evolution from 'A Happy Death' to 'The Stranger' - Camus's changing view on happiness",
    "Zagreus's theory: money, time, solitude - and why it's incomplete",
    "The monks example: happiness through will alone - the problem this creates",
    "Happiness as harmony with life vs. lucidity as seeing what IS",
    "Why Meursault's final happiness is hollow - what's missing is revolt",
    "The danger of focusing only on internal states while ignoring reality"
  ],
  "approach": "Start with the happiness question, show its evolution, then reveal the deeper issue of lucidity",
  "connections": "Connects to Mediterranean spirit (next section) and revolt against absurd (later)"
}}

Create a complete outline that takes listeners through the book's INTELLECTUAL JOURNEY.

Respond with JSON array of sections:
"""

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
    
    def process(self, source: str, max_chapters: int = 20) -> Optional[Dict[str, Any]]:
        """Complete analysis pipeline focusing on IDEAS"""
        log.info("Starting ideas-focused book analysis...")

        # Load content
        text = self.load_content(source)
        if not text:
            log.error("Failed to load content")
            return None

        log.info(f"Loaded text: {len(text)} characters (~{len(text.split())} words)")

        # Chunk text
        chunks = self.chunk_text(text, chunk_size=3000, min_size=1000)

        # Analyze themes (ideas-focused)
        themes = self.analyze_themes(text)

        # Analyze ideas (not just chapters)
        ideas = self.analyze_ideas(text, max_chapters)

        # Create outline (ideas-focused)
        outline = self.create_outline(text, themes or {}, ideas)

        result = {
            "source": source,
            "themes": themes or {},
            "ideas": ideas,  # Changed from "chapters"
            "chunks": chunks,
            "outline": outline or [],
            "full_text": text,
            "metadata": {
                "total_length": len(text),
                "word_count": len(text.split()),
                "num_chunks": len(chunks),
                "num_ideas": len(ideas),
                "num_sections": len(outline) if outline else 0,
                "content_type": themes.get("tradition", "unknown") if themes else "unknown"
            }
        }

        log.info("Ideas-focused analysis complete")
        return result