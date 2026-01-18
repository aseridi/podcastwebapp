"""
Podcast Script Generator - NEW APPROACH
Generates scripts that EXPLORE philosophical frameworks using pre-extracted passages
NO MORE sending full text to every section!
"""
import re
import logging
from typing import Dict, Any, Optional, List
from .api_clients import DeepSeekClient

log = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates podcast scripts that explore philosophical frameworks"""
    
    def __init__(self, deepseek_client: DeepSeekClient):
        self.deepseek = deepseek_client
    
    def generate_section(self, 
                        section: Dict[str, Any],
                        framework: Dict[str, Any],
                        all_passages: List[Dict[str, str]],
                        all_examples: List[Dict[str, str]]) -> Optional[str]:
        """
        Generate section that EXPLORES the framework using pre-selected passages.
        NO FULL TEXT sent - only the passages needed for this section.
        """
        
        section_num = section.get("section_number", 0)
        title = section.get("title", "")
        focus = section.get("focus", "")
        approach = section.get("approach", "analytical")
        passages_to_use = section.get("passages_to_use", [])
        examples_to_use = section.get("examples_to_use", [])
        what_to_explore = section.get("what_to_explore", "")
        
        # Get framework info
        framework_name = framework.get("framework_name", "")
        core_thesis = framework.get("core_thesis", "")
        key_concepts = framework.get("key_concepts", [])
        
        # Filter to only the passages this section needs
        relevant_passages = []
        for passage_ref in passages_to_use:
            # Try to find matching passage
            for passage in all_passages:
                passage_content = passage.get("content", "")
                passage_type = passage.get("type", "")
                what_illustrates = passage.get("what_it_illustrates", "")
                
                # Match by content snippet or by what it illustrates
                if (passage_ref.lower() in passage_content.lower() or 
                    passage_ref.lower() in what_illustrates.lower() or
                    passage_ref.lower() in passage_type.lower()):
                    relevant_passages.append(passage)
                    break
        
        # Filter to only the examples this section needs
        relevant_examples = []
        for example_ref in examples_to_use:
            for example in all_examples:
                example_name = example.get("example_name", "")
                if example_ref.lower() in example_name.lower():
                    relevant_examples.append(example)
                    break
        
        log.info(f"Generating section {section_num}: {title}")
        log.info(f"  Using {len(relevant_passages)} passages, {len(relevant_examples)} examples")
        
        # Build passage reference for prompt
        passage_text = ""
        if relevant_passages:
            passage_text = "KEY PASSAGES TO USE:\n"
            for i, p in enumerate(relevant_passages, 1):
                passage_text += f"\n{i}. [{p.get('type', 'passage').upper()}]\n"
                passage_text += f"   Content: {p.get('content', '')}\n"
                passage_text += f"   Why critical: {p.get('why_critical', '')}\n"
                passage_text += f"   Illustrates: {p.get('what_it_illustrates', '')}\n"
        
        # Build example reference for prompt
        example_text = ""
        if relevant_examples:
            example_text = "SUPPORTING EXAMPLES TO USE:\n"
            for i, ex in enumerate(relevant_examples, 1):
                example_text += f"\n{i}. {ex.get('example_name', '')}\n"
                example_text += f"   Description: {ex.get('description', '')}\n"
                example_text += f"   How it connects: {ex.get('how_it_connects', '')}\n"
                example_text += f"   Key detail: {ex.get('key_quote_or_detail', '')}\n"
        
        prompt = f"""Write a podcast section exploring a philosophical framework - in the style of Philosophize This.

SECTION TITLE: {title}
SECTION FOCUS: {focus}

FRAMEWORK: {framework_name}
CORE THESIS: {core_thesis}
KEY CONCEPTS: {", ".join(key_concepts)}

WHAT TO EXPLORE IN THIS SECTION:
{what_to_explore}

APPROACH: {approach}

{passage_text}

{example_text}

---

CRITICAL INSTRUCTIONS - This is about EXPLORING IDEAS, not summarizing:

**YOUR GOAL:** Explore this ASPECT of the philosophical framework using the passages and examples as evidence.

**STYLE - Like Philosophize This:**
- Conversational, enthusiastic, engaging - like you're explaining to a curious friend
- Use emphasis naturally ("And THAT'S the key insight here...")
- Ask rhetorical questions ("But what does this actually MEAN for us?")
- Natural pacing - vary sentence length for rhythm
- Use everyday analogies to make abstract concepts concrete
- Build tension and curiosity
- First person voice ("I think...", "What strikes me...")
- Direct address ("You might be wondering...")

**HOW TO USE PASSAGES:**
- DON'T just quote them and move on
- DO explain WHY they matter, what they reveal
- DO connect them to the framework
- DO show how they change our understanding

**HOW TO USE EXAMPLES:**
- DON'T just describe what happens in the example
- DO show HOW the example illustrates the framework
- DO compare/contrast examples to reveal patterns
- DO extract the deeper insight each example provides

**STRUCTURE:**
1. **Hook** (2-3 paragraphs): Why does this aspect matter? Make it relatable
2. **Explain the concept** (4-6 paragraphs): What IS this aspect of the framework?
3. **Show it in action** (6-10 paragraphs): Use passages/examples to ILLUSTRATE
   - Not just description - show what it MEANS
   - Compare, contrast, build connections
4. **Deeper implications** (3-5 paragraphs): What does this reveal about the framework?
5. **Transition** (1-2 paragraphs): Lead into next aspect/section

**BALANCE:**
✅ 70% exploring the philosophical IDEAS
✅ 30% using passages/examples as evidence

❌ NOT 70% describing passages/examples with 30% commentary

**EXAMPLES OF GOOD vs BAD:**

❌ BAD (too descriptive):
"Nietzsche talks about true world theories. He gives the example of Plato's forms. Plato believed in ideal forms. Then Nietzsche discusses Christianity. Christianity has heaven. Then he talks about Hinduism."

✅ GOOD (idea-focused):
"Here's what's fascinating - when you look at Plato, Christianity, and Hinduism side by side, a pattern emerges. They're all doing the SAME thing. Each one says: 'This world you're living in? It's not the real one. There's another world that's more important.' Plato calls it the world of forms. Christianity calls it heaven. Hinduism talks about Brahman or unity with the universal spirit. Different names, but the same psychological move. Why? Because, as Nietzsche points out, this is a universal human problem - and we keep inventing the same solution."

**VOICE:**
- Genuine enthusiasm about ideas ("This is subtle but REALLY important...")
- Okay to show complexity ("Now, this gets tricky...")
- Natural, conversational flow
- Building understanding step by step

**LENGTH:** 3000-5000 words

**FINAL CHECK:**
- Does this explore the FRAMEWORK ASPECT clearly? ✅
- Would someone understand the concept without having read the source? ✅
- Are passages/examples used as EVIDENCE, not the main content? ✅
- Does this build on or connect to the overall framework? ✅

Now write this section exploring the framework:
"""

        return self.deepseek.generate(prompt, temperature=0.85, max_tokens=8192)

    def generate_from_outline(self, 
                             analysis: Dict[str, Any],
                             podcast_name: str = "My Podcast",
                             host_name: str = "Host") -> Optional[str]:
        """
        Generate complete script by processing outline section by section.
        Uses framework + passages + examples (NOT full text).
        """
        
        framework = analysis.get("framework", {})
        passages = analysis.get("key_passages", [])
        examples = analysis.get("supporting_examples", [])
        outline = analysis.get("outline", [])
        
        if not outline:
            log.error("No outline found in analysis")
            return None
        
        if not framework:
            log.error("No framework found in analysis")
            return None

        framework_name = framework.get("framework_name", "Unknown topic")
        
        log.info(f"Generating script for framework: {framework_name}")
        log.info(f"Available: {len(passages)} passages, {len(examples)} examples")
        log.info(f"Sections to generate: {len(outline)}")

        # Generate title/intro
        title = f"{podcast_name}: {framework_name}"

        # Collect all sections
        sections = []

        for section_data in outline:
            section_content = self.generate_section(
                section_data,
                framework,
                passages,
                examples
            )

            if section_content:
                sections.append(section_content)
                log.info(f"Section {section_data.get('section_number')} complete ({len(section_content)} chars)")
            else:
                log.warning(f"Section {section_data.get('section_number')} failed, skipping")

        if not sections:
            log.error("No sections were generated successfully")
            return None

        # Assemble final script
        full_script = f"{title}\n\n" + "\n\n---\n\n".join(sections)

        log.info(f"Complete script generated: {len(full_script)} characters, {len(sections)} sections")
        return full_script

    def polish(self, script: str) -> Optional[str]:
        """
        Final polish for philosophical podcast script.
        Focus on flow, clarity, and spoken delivery.
        """
        log.info("Polishing philosophical podcast script...")

        prompt = f"""Polish this podcast script about a philosophical framework:

GOALS:
1. Fix grammatical errors and awkward phrasing
2. Improve flow for SPOKEN delivery (this will be read aloud)
3. Remove redundancy or repetitive explanations
4. Ensure consistent conversational tone (like Philosophize This)
5. Strengthen transitions between ideas
6. Make sure abstract concepts are explained clearly
7. Verify quotes and references are accurate and properly contextualized

MAINTAIN:
- The enthusiastic, conversational voice
- First-person perspective and direct address
- Rhetorical questions and natural emphasis
- The focus on IDEAS over plot/events
- The balance between explanation and evidence

CRITICAL INSTRUCTIONS:
- Output ONLY the refined transcript text itself
- Do NOT add meta-commentary (like "Here is the polished version")
- Do NOT add stage directions, sound cues, or text in parentheses/asterisks
- Do NOT add speaker labels like "HOST:" or "NARRATOR:"
- Do NOT add markdown formatting (###, **, etc.)
- Do NOT add section breaks beyond what's already there
- Keep the same overall length and structure
- Maintain the conversational, podcast-friendly tone

SCRIPT TO POLISH:
{script}

Return only the polished script with no additional commentary or formatting:
"""

        return self.deepseek.generate(prompt, temperature=0.6, max_tokens=8192)

    def clean_output(self, text: str) -> str:
        """Remove unwanted formatting and meta-commentary"""
        
        # Remove meta-commentary at start
        text = re.sub(r'^.*?Here is.*?(?:script|transcript|version).*?\n+', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove stage directions in parentheses or asterisks
        text = re.sub(r'\*\*\(.*?\)\*\*', '', text)
        text = re.sub(r'\(SOUND.*?\)', '', text, flags=re.IGNORECASE)
        
        # Remove speaker labels
        text = re.sub(r'\*\*HOST:\*\*|\*\*NARRATOR:\*\*', '', text, flags=re.IGNORECASE)
        
        # Remove markdown headers
        text = re.sub(r'###\s*', '', text)
        
        # Remove excessive asterisks
        text = re.sub(r'\*{2,}', '', text)
        
        # Clean up multiple newlines (but preserve section breaks)
        text = re.sub(r'\n{4,}', '\n\n---\n\n', text)
        text = re.sub(r'\n{3}', '\n\n', text)
        
        return text.strip()
    
    def generate_complete(self, 
                         analysis: Dict[str, Any], 
                         podcast_name: str = "My Podcast",
                         host_name: str = "Host",
                         skip_elaborate: bool = False,
                         skip_polish: bool = False) -> Optional[str]:
        """
        Generate complete script through all stages.
        Now works with framework + passages (not full text).
        """
        log.info("Starting complete script generation pipeline...")
        
        # Generate script from outline (using framework + passages)
        script = self.generate_from_outline(analysis, podcast_name, host_name)
        if not script:
            log.error("Failed to generate script from outline")
            return None
        
        log.info(f"Script generated: {len(script)} characters")
        
        # Skip elaborate step (we removed this approach)
        
        # Polish if requested
        if skip_polish:
            log.info("Skipping polish step")
            return self.clean_output(script)
        
        polished = self.polish(script)
        if not polished:
            log.warning("Polishing failed, using unpolished version")
            return self.clean_output(script)

        # Clean output
        polished = self.clean_output(polished)
        
        log.info(f"Script polished: {len(polished)} characters")
        return polished