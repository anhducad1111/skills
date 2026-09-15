"""
convert.py — Programmatic MarkItDown conversion with optional LLM visual description.
Usage:
    python convert.py input.pdf -o output.md
    python convert.py presentation.pptx -o presentation.md --use-llm
"""
import os
import sys
import argparse
import warnings

# Suppress audio/ffmpeg warnings from pydub
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ["PYTHONWARNINGS"] = "ignore"

from markitdown import MarkItDown

def main():
    parser = argparse.ArgumentParser(description="Convert files to Markdown via MarkItDown")
    parser.add_argument("input", help="Input file path or URL")
    parser.add_argument("-o", "--output", help="Output file path (prints to stdout if omitted)")
    parser.add_argument("-d", "--use-docintel", action="store_true", help="Use Azure Document Intelligence")
    parser.add_argument("-e", "--endpoint", help="Azure Document Intelligence Endpoint")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for image descriptions (requires OPENAI_API_KEY)")
    parser.add_argument("--model", default="gpt-4o", help="Model name for image description (default: gpt-4o)")
    parser.add_argument("--keep-data-uris", action="store_true", help="Keep base64 data URIs inline")

    args = parser.parse_args()

    llm_client = None
    if args.use_llm:
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
            base_url = "https://openrouter.ai/api/v1" if os.getenv("OPENROUTER_API_KEY") and not os.getenv("OPENAI_API_KEY") else None
            llm_client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            print("Warning: openai package not installed. Skipping LLM image description.", file=sys.stderr)

    docintel_endpoint = args.endpoint or os.getenv("MARKITDOWN_DOCINTEL_ENDPOINT")
    md = MarkItDown(
        docintel_endpoint=docintel_endpoint if args.use_docintel else None,
        llm_client=llm_client,
        llm_model=args.model if llm_client else None,
        enable_plugins=True
    )

    try:
        result = md.convert(args.input)
        content = result.text_content

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Converted '{args.input}' -> '{args.output}'")
        else:
            print(content)
    except Exception as e:
        print(f"Error converting '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
