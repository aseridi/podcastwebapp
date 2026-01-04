"""
Text-to-Speech Generator using Gemini TTS
Converts podcast scripts to audio files
"""

import logging
import mimetypes
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional
from google import genai
from google.genai import types

log = logging.getLogger(__name__)


class TTSGenerator:
    """Generates audio from text using Gemini TTS"""
    
    # Available voices in Gemini TTS
    VOICES = [
        "Zephyr",    # Bright
        "Puck",      # Upbeat  
        "Charon",    # Informative
        "Kore",      # Firm
        "Fenrir",    # Excitable
        "Leda",      # Youthful
        "Orus",      # Firm
        "Aoede",     # Breezy
        "Callirrhoe",# Easy-going
        "Autonoe",   # Bright
        "Enceladus", # Breathy
        "Iapetus",   # Clear
        "Umbriel",   # Easy-going
        "Algieba",   # Smooth
        "Despina",   # Smooth
        "Erinome",   # Clear
        "Algenib",   # Gravelly
        "Rasalgethi",# Informative
        "Laomedeia", # Upbeat
        "Achernar",  # Soft
        "Alnilam",   # Firm
        "Schedar",   # Even
        "Gacrux",    # Mature
        "Pulcherrima",# Forward
        "Achird",    # Friendly
        "Zubenelgenubi",# Casual
        "Vindemiatrix",# Gentle
        "Sadachbia", # Lively
        "Sadaltager",# Knowledgeable
        "Sulafat",   # Warm
    ]
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro-preview-tts"):
        """Initialize TTS generator
        
        Args:
            api_key: Google API key
            model: TTS model to use
        """
        if not api_key:
            raise ValueError("Google API key is required for TTS")
        
        self.client = genai.Client(api_key=api_key)
        self.model = model
        log.info(f"TTS Generator initialized with model: {model}")
    
    def generate_audio(
        self,
        text: str,
        output_path: Path,
        voice: str = "Schedar",
        temperature: float = 0.87
    ) -> Optional[Path]:
        """Generate audio from text
        
        Args:
            text: The script text to convert to speech
            output_path: Directory to save the audio file
            voice: Voice name to use (see VOICES list)
            temperature: Controls expressiveness (0.0-2.0, default 1.0)
        
        Returns:
            Path to the generated audio file, or None on failure
        """
        if voice not in self.VOICES:
            log.warning(f"Unknown voice '{voice}', defaulting to 'Schedar'")
            voice = "Schedar"
        
        log.info(f"Generating audio with voice '{voice}', temperature {temperature}")
        log.info(f"Text length: {len(text)} characters")
        
        try:
            # Prepare the content
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=text)],
                ),
            ]
            
            # Configure generation
            config = types.GenerateContentConfig(
                temperature=temperature,
                response_modalities=["audio"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                ),
            )
            
            # Collect audio chunks
            audio_chunks = []
            mime_type = None
            
            for chunk in self.client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                # Skip empty chunks
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                part = chunk.candidates[0].content.parts[0]
                
                if part.inline_data and part.inline_data.data:
                    audio_chunks.append(part.inline_data.data)
                    if mime_type is None:
                        mime_type = part.inline_data.mime_type
            
            if not audio_chunks:
                log.error("No audio data received from TTS")
                return None
            
            # Combine all chunks
            combined_audio = b"".join(audio_chunks)
            log.info(f"Received {len(combined_audio)} bytes of audio data")
            
            # Convert to WAV format
            wav_data = self._convert_to_wav(combined_audio, mime_type or "audio/L16;rate=24000")
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"podcast_audio_{timestamp}.wav"
            file_path = output_path / filename
            
            # Save file
            file_path.write_bytes(wav_data)
            log.info(f"Audio saved to: {file_path}")
            
            return file_path
            
        except Exception as e:
            log.error(f"TTS generation failed: {e}", exc_info=True)
            return None
    
    def _convert_to_wav(self, audio_data: bytes, mime_type: str) -> bytes:
        """Convert raw audio data to WAV format
        
        Args:
            audio_data: Raw audio bytes
            mime_type: MIME type with encoding info
        
        Returns:
            WAV file bytes with proper header
        """
        params = self._parse_audio_mime_type(mime_type)
        bits_per_sample = params["bits_per_sample"]
        sample_rate = params["rate"]
        num_channels = 1
        
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size
        
        # WAV header structure
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (PCM)
            1,                # AudioFormat (PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size
        )
        
        return header + audio_data
    
    def _parse_audio_mime_type(self, mime_type: str) -> dict:
        """Parse audio parameters from MIME type
        
        Args:
            mime_type: e.g., "audio/L16;rate=24000"
        
        Returns:
            Dict with bits_per_sample and rate
        """
        bits_per_sample = 16
        rate = 24000
        
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate = int(param.split("=", 1)[1])
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass
        
        return {"bits_per_sample": bits_per_sample, "rate": rate}