"""
Text Analysis and Structuring - NEW APPROACH
Analyzes input text to identify ONE philosophical framework and extract key passages
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
    """Analyzes text content focusing on ONE philosophical framework"""
    
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
            downloaded = trafilatura.fetch_url(url)
            
            if downloaded is None:
                log.warning(f"Empty response from {url}")
                return None

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
    
    def identify_framework(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Identify the ONE philosophical framework the text operates within.
        This is NOT about extracting multiple ideas - it's about finding the central lens/worldview.
        """
        log.info("Identifying philosophical framework...")
        
        prompt = f"""Analyze this text to identify the SINGLE philosophical framework it operates within.

CRITICAL: We're not looking for multiple separate ideas. We're identifying the ONE central worldview/lens through which the author views everything.

Examples:
- Nietzsche → Anti-nihilism, critique of morality, will to power
- Sartre → Existentialism (existence precedes essence, radical freedom)
- Camus → Absurdism (living authentically without escape from meaninglessness)
- Kafka → Alienation under bureaucratic/authoritarian systems

Text (first section):
{text[:8000]}

Respond with JSON containing:

{{
  "framework_name": "The name of the philosophical framework/worldview",
  
  "tradition": "What philosophical tradition does this belong to? (Existentialism, Stoicism, etc.)",
  
  "core_thesis": "In 2-3 sentences, what is the CENTRAL argument/worldview? What lens does everything get viewed through?",
  
  "how_author_explores": "How does the author explore this framework? Through narrative? Critique? Comparison? Lived examples?",
  
  "key_concepts": [
    "3-5 essential concepts that are part of this framework (e.g., for Nietzsche: 'slave morality', 'true world theories', 'will to power')"
  ]
}}

Example response for Nietzsche's work:
{{
  "framework_name": "Critique of Morality and True World Theories",
  "tradition": "Existentialism, German philosophy, Anti-Christianity",
  "core_thesis": "Humans invent 'true worlds' (afterlife, Platonic forms, religious heavens) to escape the psychological burden of meaninglessness. This invention breeds complacency and prevents authentic living by justifying weakness as virtue.",
  "how_author_explores": "Through systematic critique of Christianity and comparison to other religions/philosophies, showing how they all follow the same pattern of escaping reality",
  "key_concepts": [
    "True world theories",
    "Slave morality", 
    "God is dead",
    "Christianity as narcotic"
  ]
}}

Now identify the framework for this text:
"""

        response = self.gemini.generate(prompt, temperature=0.6)
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
            log.error(f"Failed to parse framework JSON: {e}")

        return None
    
    def extract_key_passages(self, text: str, framework: Dict[str, Any], 
                           max_passages: int = 12) -> List[Dict[str, str]]:
        """
        Extract KEY PASSAGES (quotes, analogies, examples) that crystallize the framework.
        These are the "God is dead" moments - the passages that capture the essence.
        """
        log.info(f"Extracting up to {max_passages} key passages that crystallize the framework...")
        
        framework_name = framework.get("framework_name", "")
        core_thesis = framework.get("core_thesis", "")
        key_concepts = framework.get("key_concepts", [])
        
        prompt = f"""Extract the most CRITICAL passages from this text that crystallize the philosophical framework.

FRAMEWORK: {framework_name}
CORE THESIS: {core_thesis}
KEY CONCEPTS: {", ".join(key_concepts)}

We need passages that:
1. **Famous quotes** that capture the essence ("God is dead and we have killed him")
2. **Powerful analogies** that make abstract concepts concrete (carts/wagons = true world theories)
3. **Concrete examples** that illustrate the framework (Plato's forms, Christian heaven)
4. **Critical arguments** that build the case

Extract {max_passages} passages total.

Text to analyze:
{text[:15000]}

For EACH passage provide:

{{
  "type": "quote" | "analogy" | "example" | "argument",
  
  "content": "The actual quote, analogy, or example text",
  
  "location": "Where it appears (chapter/section/page if known)",
  
  "why_critical": "Why is this passage essential to understanding the framework? What does it crystallize?",
  
  "what_it_illustrates": "What aspect of the framework does this show? How does it connect to the core thesis?"
}}

Example for Nietzsche:
[
  {{
    "type": "quote",
    "content": "God is dead. God remains dead. And we have killed him. How shall we comfort ourselves, the murderer of all murderers?",
    "location": "The Gay Science, Section 125",
    "why_critical": "The pivotal declaration. Not celebration but lament - shows Nietzsche's fear about humanity losing moral compass",
    "what_it_illustrates": "The death of humanity's pursuit for objective morality through true world theories"
  }},
  {{
    "type": "analogy",
    "content": "Carrying heavy stuff is a universal problem → humans invented carts, wagons, wheels. Meaning of life is a universal problem → humans invented true world theories (heaven, forms, etc.)",
    "location": "Middle section",
    "why_critical": "Makes the abstract concrete - shows true worlds as psychological tools, not divine revelations",
    "what_it_illustrates": "True world theories are human inventions to solve existential burden, just like carts solve physical burden"
  }},
  {{
    "type": "example",
    "content": "Christianity's 'slave morality' - turning weakness into virtue. 'The meek shall inherit the earth', 'Camel through eye of needle', etc.",
    "location": "Christianity critique section",
    "why_critical": "Concrete demonstration of how true world theories justify passivity",
    "what_it_illustrates": "How Christianity specifically operates as a true world theory by making weakness virtuous"
  }}
]

Respond with JSON array of passages:
"""

        response = self.deepseek.generate(prompt, temperature=0.7, max_tokens=6000)
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
            log.error(f"Failed to parse passages JSON: {e}")

        return []
    
    def extract_supporting_examples(self, text: str, framework: Dict[str, Any],
                                   passages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Extract supporting examples that illustrate the framework.
        These are NOT separate ideas - they're different angles on the SAME framework.
        """
        log.info("Extracting supporting examples...")
        
        framework_name = framework.get("framework_name", "")
        core_thesis = framework.get("core_thesis", "")
        
        # Get passage summaries for context
        passage_summaries = [p.get("what_it_illustrates", "") for p in passages[:5]]
        
        prompt = f"""Identify 5-8 supporting examples from this text that illustrate the framework from different angles.

FRAMEWORK: {framework_name}
CORE THESIS: {core_thesis}

We already have these key passages:
{chr(10).join(f"- {s}" for s in passage_summaries)}

Now find SUPPORTING EXAMPLES - different ways the author illustrates the same framework:

Text:
{text[:12000]}

For each example provide:

{{
  "example_name": "Brief name (e.g., 'Plato's World of Forms', 'Christian Heaven vs Earth')",
  
  "description": "1-2 sentences describing this example",
  
  "how_it_connects": "How does this example connect to the central framework? What angle does it provide?",
  
  "key_quote_or_detail": "A memorable quote or detail from this example"
}}

Example for Nietzsche:
[
  {{
    "example_name": "Plato's World of Forms",
    "description": "Plato posited an ideal realm of perfect forms, with our physical world being mere shadows/reflections of those ideals",
    "how_it_connects": "First major 'true world theory' in Western philosophy - establishes the pattern of denigrating this world in favor of an ideal one",
    "key_quote_or_detail": "Everything in the world is a crude reflection of some ideal form"
  }},
  {{
    "example_name": "Christian Heaven as Reward",
    "description": "Christianity presents earthly life as temporary ethical test, with heaven as the real, eternal destination",
    "how_it_connects": "Most familiar true world theory - justifies suffering in this world by promising perfection in the next",
    "key_quote_or_detail": "You spend 70-80 years in this world and eternity in the other"
  }}
]

Respond with JSON array:
"""

        response = self.gemini.generate(prompt, temperature=0.7)
        if not response:
            return []

        # Parse JSON
        try:
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            first_bracket = response.find('[')
            last_bracket = response.rfind(']')
            if first_bracket != -1 and last_bracket != -1:
                return json.loads(response[first_bracket:last_bracket + 1])
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse examples JSON: {e}")

        return []
    
    def create_outline(self, framework: Dict[str, Any], 
                      passages: List[Dict[str, str]],
                      examples: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """
        Create outline that EXPLORES the framework from different angles.
        Each section = different way of looking at the central framework.
        NOT chapter summaries - EXPLORATIONS of the worldview.
        """
        log.info("Creating framework exploration outline...")
        
        framework_name = framework.get("framework_name", "")
        core_thesis = framework.get("core_thesis", "")
        key_concepts = framework.get("key_concepts", [])
        
        # Organize passages by type for the outline
        quotes = [p for p in passages if p.get("type") == "quote"]
        analogies = [p for p in passages if p.get("type") == "analogy"]
        
        prompt = f"""Create a podcast outline that EXPLORES this philosophical framework from different angles.

FRAMEWORK: {framework_name}
CORE THESIS: {core_thesis}
KEY CONCEPTS: {", ".join(key_concepts)}

AVAILABLE PASSAGES TO USE:
{json.dumps(passages[:8], indent=2)}

AVAILABLE EXAMPLES:
{json.dumps(examples[:6], indent=2)}

Create 5-8 sections that explore the framework. Think like Philosophize This podcast:

**Section Flow:**
1. **Hook/Problem** - Why does this framework matter? What problem does it address?
2. **Define the Framework** - What IS this worldview? Make it clear and concrete
3. **Show How It Works** - Use examples/passages to illustrate (NOT plot summary)
4. **Contrast and Compare** - How is this different from other approaches?
5. **Implications** - What does this mean for how we live/think?

Each section should:
- Focus on exploring the FRAMEWORK (not recapping events)
- Use passages/examples as EVIDENCE (not as the main content)
- Build on previous sections
- Connect back to the core thesis

For each section provide:

{{
  "section_number": 1,
  
  "title": "Engaging title about exploring an ASPECT of the framework (not 'Chapter 1-3 Summary')",
  
  "focus": "What aspect of the framework does this section explore?",
  
  "approach": "How should this be presented? (analytical, storytelling, compare/contrast, build tension, etc.)",
  
  "passages_to_use": ["List 2-4 passage contents or types that illustrate this aspect"],
  
  "examples_to_use": ["List 1-3 example names that support this section"],
  
  "what_to_explore": "What questions should this section answer? What understanding should listener gain?",
  
  "connection_to_next": "How does this section lead into the next exploration?"
}}

Example section for Nietzsche:
{{
  "section_number": 2,
  "title": "The Pattern Emerges: Why Every Religion Looks the Same",
  "focus": "Showing that all major religions/philosophies follow the same 'true world theory' formula",
  "approach": "Compare and contrast multiple examples to reveal the pattern",
  "passages_to_use": [
    "Carts and wagons analogy - universal problems get universal solutions",
    "Plato's forms example",
    "Christian heaven example"
  ],
  "examples_to_use": ["Plato's World of Forms", "Christian Heaven", "Hindu Brahman"],
  "what_to_explore": "Why do completely different cultures arrive at the same solution? What does this tell us about human psychology? The formula: reject this world, posit a better one",
  "connection_to_next": "Once we see the pattern, we can understand why Nietzsche says 'God is dead' - and why he's terrified"
}}

Create a complete outline exploring the framework:
"""

        response = self.gemini.generate(prompt, temperature=0.7, max_tokens=6000)
        if not response:
            log.error("No response from Gemini for outline generation")
            return None

        # Parse JSON array
        try:
            # Try to extract from markdown code block (use greedy match for nested arrays)
            json_match = re.search(r'```json\s*(\[[\s\S]*\])\s*```', response)
            if json_match:
                return json.loads(json_match.group(1))

            # Fallback: find outermost brackets
            first_bracket = response.find('[')
            last_bracket = response.rfind(']')
            if first_bracket != -1 and last_bracket != -1:
                return json.loads(response[first_bracket:last_bracket + 1])

            log.error(f"No JSON array found in outline response. Response start: {response[:300]}...")
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse outline JSON: {e}")
            log.error(f"Response was: {response[:500]}...")

        return None
    
    def process(self, source: str, max_passages: int = 12) -> Optional[Dict[str, Any]]:
        """
        Complete analysis pipeline focusing on ONE philosophical framework.
        NO MORE storing full text 3 times. NO MORE chunking that isn't used.
        """
        log.info("Starting philosophical framework analysis...")

        # Load content
        text = self.load_content(source)
        if not text:
            log.error("Failed to load content")
            return None

        log.info(f"Loaded text: {len(text)} characters (~{len(text.split())} words)")

        # Step 1: Identify the ONE philosophical framework
        framework = self.identify_framework(text)
        if not framework:
            log.error("Failed to identify philosophical framework")
            return None
        
        log.info(f"Framework identified: {framework.get('framework_name')}")

        # Step 2: Extract key passages that crystallize the framework
        passages = self.extract_key_passages(text, framework, max_passages)
        if not passages:
            log.warning("No key passages extracted")
        
        log.info(f"Extracted {len(passages)} key passages")

        # Step 3: Extract supporting examples
        examples = self.extract_supporting_examples(text, framework, passages)
        if not examples:
            log.warning("No supporting examples extracted")
        
        log.info(f"Extracted {len(examples)} supporting examples")

        # Step 4: Create outline for exploring the framework
        outline = self.create_outline(framework, passages, examples)
        if not outline:
            log.error("Failed to create outline")
            return None
        
        log.info(f"Created outline with {len(outline)} sections")

        # Build result - NO full text duplication!
        result = {
            "source": source[:200],  # Just reference, not full text
            "framework": framework,
            "key_passages": passages,
            "supporting_examples": examples,
            "outline": outline,
            "metadata": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "num_passages": len(passages),
                "num_examples": len(examples),
                "num_sections": len(outline),
                "framework_name": framework.get("framework_name", "unknown")
            }
        }

        log.info("Framework-focused analysis complete")
        return result