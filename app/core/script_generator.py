"""
Podcast Script Generator
Generates, elaborates, and polishes podcast scripts
"""
import re
import logging
from typing import Dict, Any, Optional, List
from .api_clients import DeepSeekClient

log = logging.getLogger(__name__)


class ScriptGenerator:
    """Generates podcast scripts from analyzed content"""
    
    def __init__(self, deepseek_client: DeepSeekClient):
        self.deepseek = deepseek_client
    
    def generate_section(self, section: Dict[str, Any], theme: str,
                        full_text: str, ideas: List[Dict[str, Any]]) -> Optional[str]:
        """Generate section that EXPLORES IDEAS, not plot summary"""

        section_num = section.get("section_number", 0)
        title = section.get("title", "")
        main_idea = section.get("main_idea", "")
        key_points = section.get("key_points", [])
        approach = section.get("approach", "analytical")
        connections = section.get("connections", "")

        log.info(f"Generating ideas-focused section {section_num}: {title}")

        prompt = f"""Write a podcast section exploring an IDEA from a book - in the style of Philosophize This.

SECTION TITLE: {title}
MAIN IDEA TO EXPLORE: {main_idea}

KEY POINTS TO DISCUSS:
{chr(10).join(f"- {point}" for point in key_points)}

APPROACH: {approach}
CONNECTIONS: {connections}

BOOK'S CENTRAL THEME: {theme}

SOURCE MATERIAL (use as examples, not to summarize):
{full_text[:12000]}

---

CRITICAL INSTRUCTIONS - Read carefully:

**YOUR GOAL:** Explore the IDEA/CONCEPT, not retell the plot.

**STYLE - Like Philosophize This:**
- Conversational, enthusiastic, engaging
- Use emphasis naturally ("And THAT'S the key point here...")
- Ask rhetorical questions ("But what does this MEAN?")
- Make it feel like you're having a fascinating conversation
- Use everyday examples and analogies
- Build tension and curiosity
- Vary sentence length for rhythm

**STRUCTURE:**
1. **Hook** (2-3 paragraphs): Why does this idea matter? Make it relevant.
2. **Explain the concept** (4-6 paragraphs): What IS this idea? Break it down clearly.
3. **Show how the book explores it** (5-8 paragraphs): Use characters/plot as EXAMPLES
   - Don't just retell events
   - Show how events ILLUSTRATE the idea
4. **Contrast and compare** (3-5 paragraphs): How is this different from other approaches?
5. **Implications** (3-4 paragraphs): What does this mean for how we live/think?
6. **Transition** (1-2 paragraphs): Connect to what's coming next

**BALANCE:**
✅ 70% discussing the IDEA itself
✅ 30% using book examples to illustrate

❌ NOT 70% plot summary with 30% commentary

**EXAMPLES OF GOOD vs BAD:**

❌ BAD (too plot-focused):
"In Chapter 3, Meursault goes to his mother's funeral. He doesn't cry. Then he goes to the beach. There he meets a man with a knife. The sun is in his eyes. He shoots the man. This shows he's detached."

✅ GOOD (idea-focused):
"Let's talk about what Camus means by 'the absurd.' It's not just meaninglessness - it's the TENSION between what we need and what reality provides. Now, how does he show this? Look at Meursault at his mother's funeral. He's more aware of the heat than his grief. Why? Because Camus is showing us someone who's found one way to deal with the absurd: complete detachment. But here's the thing - this ISN'T the answer Camus is proposing..."

**USE BOOK STRATEGICALLY:**
- Pick 2-3 vivid scenes/moments that ILLUSTRATE the idea
- Explain WHY these moments matter philosophically
- Don't worry about comprehensive plot coverage

**VOICE:**
- First person ("I think...", "What strikes me...")
- Direct address ("You might be wondering...")
- Genuine enthusiasm about ideas
- Okay to admit complexity ("This is subtle but important...")

**LENGTH:** 3000-5000 words

**FINAL CHECK:**
- Could someone understand the IDEA without reading the book? ✅
- Are you exploring concepts, not just recapping events? ✅
- Would this work as a standalone discussion of the idea? ✅

Now write this section exploring the idea:
"""

        return self.deepseek.generate(prompt, temperature=0.8, max_tokens=8192)

    def generate_from_outline(self, analysis: Dict[str, Any],
                             podcast_name: str = "My Podcast",
                             host_name: str = "Host") -> Optional[str]:
        """Generate complete content by processing outline section by section"""

        outline = analysis.get("outline", [])
        if not outline:
            log.error("No outline found in analysis")
            return None

        theme = analysis.get("themes", {}).get("central_question", "Unknown topic")
        ideas = analysis.get("ideas", [])
        full_text = analysis.get("full_text", "")

        log.info(f"Generating content with {len(outline)} sections...")

        # Generate title
        title = f"Episode: {theme}"

        # Collect all sections
        sections = []

        for section_data in outline:
            section_content = self.generate_section(
                section_data,
                theme,
                full_text,
                ideas
            )

            if section_content:
                sections.append(section_content)
                log.info(f"Section {section_data.get('section_number')} complete")
            else:
                log.warning(f"Section {section_data.get('section_number')} failed, skipping")

        if not sections:
            log.error("No sections were generated successfully")
            return None

        # Assemble final content
        full_content = f"{title}\n\n" + "\n\n".join(sections)

        log.info(f"Complete content generated: {len(full_content)} characters")
        return full_content

    def polish(self, script: str) -> Optional[str]:
        """Final polish and cleanup for book-based podcast"""
        log.info("Polishing book podcast script...")

        prompt = f"""Polish this podcast transcript about a book by:

1. Fixing any grammatical errors or awkward phrasing
2. Improving sentence flow and readability for spoken delivery
3. Removing any redundancy or repetitive explanations
4. Ensuring consistent tone throughout (engaging but respectful of the source material)
5. Strengthening the opening hook and closing reflection
6. Ensuring smooth transitions between topics and sections
7. Balancing summary with analysis - make sure it's not just a book report
8. Verifying that quotes or references to the book are clear and accurate

CRITICAL INSTRUCTIONS:
- Output ONLY the refined transcript text itself
- Do NOT add meta-commentary (like "Here is the polished version")
- Do NOT add stage directions, sound cues, or text in parentheses/asterisks
- Do NOT add speaker labels like "HOST:" or "NARRATOR:"
- Do NOT add markdown formatting (###, **, etc.)
- Do NOT add section breaks or episode markers
- Keep the same overall length and structure
- Maintain the conversational, podcast-friendly tone
- Preserve all book references and examples

TRANSCRIPT TO POLISH:
{script}

Return only the polished transcript with no additional commentary or formatting:
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
        
        # Clean up multiple newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def generate_complete(self, analysis: Dict[str, Any], 
                         podcast_name: str = "My Podcast",
                         host_name: str = "Host",
                         skip_elaborate: bool = False,
                         skip_polish: bool = False) -> Optional[str]:
        """Generate complete content through all stages"""
        log.info("Starting complete content generation pipeline...")
        
        # Generate content from outline
        content = self.generate_from_outline(analysis, podcast_name, host_name)
        if not content:
            log.error("Failed to generate content from outline")
            return None
        
        log.info(f"Content generated: {len(content)} characters")
        
        # Skip elaborate (we're not using it anymore)
        if skip_polish:
            return content
        
        # Polish
        polished = self.polish(content)
        if not polished:
            log.warning("Polishing failed, using unpolished version")
            return content

        # Clean output
        polished = self.clean_output(polished)
        
        log.info(f"Content polished: {len(polished)} characters")
        return polished