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
                        full_text: str, concepts: List[Dict[str, Any]]) -> Optional[str]:
        """Generate content for one outline section"""
        
        section_num = section.get("section_number", 0)
        title = section.get("title", "")
        focus = section.get("focus", "")
        key_points = section.get("key_points", [])
        
        log.info(f"Generating section {section_num}: {title}")
        
        # Build prompt for this specific section
        prompt = f"""Write a section of a podcast monologue about: {title}

MAIN THEME: {theme}
SECTION FOCUS: {focus}
KEY POINTS TO COVER:
{chr(10).join(f"- {point}" for point in key_points)}

RELEVANT SOURCE MATERIAL:
{full_text[:8000]}

Write this section in a natural, conversational tone as if you're speaking directly to the listener.
- Use first person ("I want to talk about...")
- Include specific examples and details from the source material
- Make it engaging with analogies, questions, or stories
- This should be 300-500 words
- Flow naturally but stay focused on this section's topic

Write ONLY this section, not the entire episode."""

        return self.deepseek.generate(prompt, temperature=0.8, max_tokens=4096)

    def generate_from_outline(self, analysis: Dict[str, Any], 
                             podcast_name: str = "My Podcast",
                             host_name: str = "Host") -> Optional[str]:
        """Generate complete content by processing outline section by section"""
        
        outline = analysis.get("outline", [])
        if not outline:
            log.error("No outline found in analysis")
            return None
        
        theme = analysis.get("themes", {}).get("theme", "Unknown topic")
        concepts = analysis.get("concepts", [])
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
                concepts
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
        """Final polish and cleanup"""
        log.info("Polishing script...")
        
        prompt = f"""Polish this podcast transcript by:

    1. Fixing any grammatical errors
    2. Improving sentence flow and readability
    3. Removing redundancy
    4. Ensuring consistent tone
    5. Strengthening the opening and closing
    6. Making sure transitions are smooth

    CRITICAL INSTRUCTIONS:
    - Do NOT add any meta-commentary (like "Here is the polished version")
    - Do NOT add stage directions, sound cues, or any text in parentheses or asterisks
    - Do NOT add speaker labels like "HOST:" or "NARRATOR:"
    - Do NOT add any markdown formatting (###, **, etc.)
    - Output ONLY the refined transcript text itself
    - Keep the same length and structure

    TRANSCRIPT:
    {script}

    Return only the polished transcript with no additional commentary."""

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