#!/usr/bin/env python
"""
Command-line interface for Podcast Script Generator
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import API_KEYS, PIPELINE_CONFIG, OUTPUT_DIR
from app.core.pipeline import PodcastPipeline


def main():
    parser = argparse.ArgumentParser(
        description='Generate podcast scripts from content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -s "Your content here" -n "My Show" -h "Jane Doe"
  %(prog)s -s https://example.com/article -n "Tech Talk"
  %(prog)s -s input.txt -o custom_output.txt --fast
        """
    )
    
    # Required arguments
    parser.add_argument(
        '-s', '--source',
        required=True,
        help='Content source (text, file path, or URL)'
    )
    
    # Optional arguments
    parser.add_argument(
        '-n', '--name',
        default='My Podcast',
        help='Podcast name (default: My Podcast)'
    )
    
    parser.add_argument(
        '-t', '--host',
        default='Host',
        help='Host name (default: Host)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: auto-generated in outputs/scripts/)'
    )
    
    parser.add_argument(
        '-c', '--concepts',
        type=int,
        default=PIPELINE_CONFIG['max_concepts'],
        help=f'Max concepts to analyze (default: {PIPELINE_CONFIG["max_concepts"]})'
    )
    
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Fast mode: skip elaboration and polishing'
    )
    
    parser.add_argument(
        '--skip-elaborate',
        action='store_true',
        help='Skip elaboration step'
    )
    
    parser.add_argument(
        '--skip-polish',
        action='store_true',
        help='Skip polishing step'
    )
    
    parser.add_argument(
        '--no-save-analysis',
        action='store_true',
        help='Do not save intermediate analysis JSON'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON'
    )
    
    args = parser.parse_args()
    
    # Validate API keys
    if not API_KEYS["google"] or not API_KEYS["deepseek"]:
        print("Error: API keys not configured. Please set GOOGLE_API_KEY and DEEPSEEK_KEY in .env file", 
              file=sys.stderr)
        sys.exit(1)
    
    # Initialize pipeline
    try:
        pipeline = PodcastPipeline(
            google_api_key=API_KEYS["google"],
            deepseek_api_key=API_KEYS["deepseek"],
            output_dir=OUTPUT_DIR
        )
    except Exception as e:
        print(f"Error initializing pipeline: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Determine skip flags
    skip_elaborate = args.skip_elaborate or args.fast
    skip_polish = args.skip_polish or args.fast
    
    # Print configuration
    if not args.json:
        print("🎙️  Podcast Script Generator")
        print("=" * 50)
        print(f"Source: {args.source[:100]}...")
        print(f"Podcast: {args.name}")
        print(f"Host: {args.host}")
        print(f"Max Concepts: {args.concepts}")
        print(f"Mode: {'Fast' if args.fast else 'Full'}")
        print("=" * 50)
        print()
    
    # Generate script
    try:
        result = pipeline.generate(
            source=args.source,
            podcast_name=args.name,
            host_name=args.host,
            max_concepts=args.concepts,
            skip_elaborate=skip_elaborate,
            skip_polish=skip_polish,
            save_intermediate=not args.no_save_analysis
        )
        
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
        
        # Handle output
        if args.json:
            # Output as JSON
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            script = result['script']
            metadata = result['metadata']
            
            # Save to custom path if specified
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(script)
                print(f"✅ Script saved to: {output_path}")
            else:
                print(f"✅ Script saved to: {result['script_file']}")
            
            # Print metadata
            print()
            print(f"📊 Statistics:")
            print(f"   - Length: {metadata['script_length']:,} characters")
            print(f"   - Words: {metadata['word_count']:,}")
            print(f"   - Concepts: {metadata['num_concepts']}")
            print(f"   - Generation time: {metadata['duration_seconds']:.1f}s")
            
            if result.get('analysis_file'):
                print(f"   - Analysis: {result['analysis_file']}")
            
            print()
            print("✨ Script generation complete!")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Generation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
