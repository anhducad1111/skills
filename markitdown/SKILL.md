---
name: markitdown
description: >-
  Use when converting non-Markdown files (PDF, Word DOCX, PowerPoint PPTX, Excel XLSX/XLS, HTML, CSV, JSON, XML, EPUB, ZIP archives, images with OCR, audio with transcription, or YouTube URLs) into clean, LLM-ready Markdown text, or when extracting structured text and tables from office documents.
---

# MarkItDown

A skill for converting office documents, PDFs, media files, and web pages into clean, token-efficient Markdown using Microsoft's [MarkItDown](https://github.com/microsoft/markitdown) CLI and Python API.

---

## When to Use

- **Office Documents**: Extracting text, tables, and outlines from Word (`.docx`), Excel (`.xlsx`, `.xls`), and PowerPoint (`.pptx`).
- **PDF Documents**: Parsing text, multi-column layouts, and tables from `.pdf` files.
- **Data & Markup Formats**: Converting `.html`, `.csv`, `.json`, and `.xml` into readable Markdown tables/blocks.
- **E-books & Archives**: Extracting content from `.epub` books and traversing `.zip` archives.
- **Audio & Video Transcripts**: Extracting audio speech transcripts from `.mp3`/`.wav` or subtitles from YouTube URLs.
- **Images with OCR**: Extracting text and metadata from `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`.

### When NOT to Use
- When the file is already a Markdown or plain text document.
- When pixel-perfect visual styling/layout reproduction is needed (use dedicated rendering/PDF engines instead).
- When binary inspection or low-level byte manipulation is required.

---

## Quick Reference (CLI)

> **Tip**: Suppress audio/ffmpeg warning on Windows by setting `$env:PYTHONWARNINGS = "ignore"`.

```powershell
# Basic conversion to stdout
$env:PYTHONWARNINGS = "ignore"; markitdown input.pdf

# Convert and save directly to a Markdown file
$env:PYTHONWARNINGS = "ignore"; markitdown document.docx -o document.md

# Convert Excel spreadsheet with tables
$env:PYTHONWARNINGS = "ignore"; markitdown data.xlsx -o data.md

# Convert from a URL (e.g. web page or YouTube)
$env:PYTHONWARNINGS = "ignore"; markitdown https://en.wikipedia.org/wiki/Markdown -o wiki.md
```

### CLI Options

| Flag | Description |
| :--- | :--- |
| `-o <file>`, `--output <file>` | Save Markdown output to specified destination file. |
| `-x <ext>`, `--extension <ext>` | Explicit file extension hint (useful when reading from stdin or generic URLs). |
| `-m <mime>`, `--mime-type <mime>` | Explicit MIME type hint. |
| `-c <charset>`, `--charset <charset>` | Explicit character set hint (default: UTF-8). |
| `-d`, `--use-docintel` | Use Azure Document Intelligence cloud service instead of local extraction. |
| `-e <url>`, `--endpoint <url>` | Azure Document Intelligence endpoint (or set `MARKITDOWN_DOCINTEL_ENDPOINT`). |
| `--keep-data-uris` | Keep base64-encoded image data URIs in output (truncated by default). |
| `-p`, `--use-plugins` | Enable third-party plugins. |
| `--list-plugins` | List all discovered MarkItDown plugins. |

---

## Helper Scripts

Ready-to-use scripts are located in the `scripts/` directory:

### 1. PowerShell Wrapper (`scripts/markitdown.ps1`)
Designed for Windows environments. Automatically handles warnings, output paths, and batch directory processing.

```powershell
# Convert a single document
.\scripts\markitdown.ps1 -InputPath "document.docx" -OutputPath "document.md"

# Convert an entire folder of mixed documents (creates markdown_output/ folder)
.\scripts\markitdown.ps1 -InputPath "C:\docs\reports\" -Recurse

# Convert using Azure Document Intelligence
.\scripts\markitdown.ps1 -InputPath "scanned.pdf" -UseDocIntel -DocIntelEndpoint "https://my-resource.cognitiveservices.azure.com/"
```

### 2. Bash Wrapper (`scripts/markitdown.sh`)
Designed for Linux, macOS, or WSL.

```bash
./scripts/markitdown.sh document.pdf output.md
./scripts/markitdown.sh /path/to/docs/
```

### 3. Python Helper (`scripts/convert.py`)
Programmatic wrapper supporting AI-assisted image description.

```bash
# Basic conversion
python scripts/convert.py document.pdf -o output.md

# AI image analysis using OpenAI / OpenRouter
python scripts/convert.py presentation.pptx -o presentation.md --use-llm --model gpt-4o
```

---

## Python API Usage

For deep integration inside Python workflows:

```python
from markitdown import MarkItDown

md = MarkItDown()

# Convert a local file
result = md.convert("financial_report.xlsx")
print(result.text_content)

# Convert from byte stream
with open("sample.pdf", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
    markdown_text = result.text_content
```

### AI-Enhanced Image Descriptions
MarkItDown can describe embedded images in PowerPoint slides or image files using an LLM:

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI() # Or OpenRouter client
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe diagrams and chart data in detail for technical documentation."
)

result = md.convert("architecture_presentation.pptx")
print(result.text_content)
```

---

## Supported Formats

| Format | Extension | Notes |
| :--- | :--- | :--- |
| **PDF** | `.pdf` | Multi-page text, tabular layouts, forms |
| **Word** | `.docx` | Headings, bold/italic, tables, bullet lists |
| **Excel** | `.xlsx`, `.xls` | Each sheet converted into Markdown tables |
| **PowerPoint** | `.pptx` | Slides, headers, bullet points, speaker notes |
| **HTML** | `.html`, `.htm` | Cleans boilerplate, navigation, scripts |
| **Data** | `.csv`, `.json`, `.xml` | Formatted structured text and tables |
| **Archives** | `.zip` | Iterates and extracts supported files within zip |
| **E-Book** | `.epub` | Full chapter text and structure |
| **Audio** | `.mp3`, `.wav` | Transcribes spoken audio |
| **Images** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | EXIF metadata + OCR text extraction |
| **Web / Video** | URLs, YouTube | Webpage content or YouTube video transcripts |

---

## Troubleshooting & Best Practices

1. **Suppressing Audio / FFmpeg Warnings**:
   If ffmpeg is not installed on Windows, running `markitdown` may trigger a `RuntimeWarning: Couldn't find ffmpeg or avconv`.
   To silence it cleanly:
   ```powershell
   $env:PYTHONWARNINGS = "ignore"
   ```

2. **Large Files / Complex PDFs**:
   If a scanned PDF has poor OCR results with offline parsers, consider switching to Azure Document Intelligence:
   ```powershell
   markitdown scanned.pdf -d -e "https://<resource>.cognitiveservices.azure.com/"
   ```

3. **Encoding Issues**:
   MarkItDown emits UTF-8 text. When piping in PowerShell 5.1, pipe output might default to UTF-16. Use the `-o` argument instead of shell redirection `>` to ensure strict UTF-8 output without BOM anomalies.
