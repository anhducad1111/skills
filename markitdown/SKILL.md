---
name: markitdown
description: Convert PDF, Office documents (Word, Excel, PowerPoint), HTML, audio, and image files into Markdown format for LLM analysis.
---

# MarkItDown

Convert various file formats (PDF, PPTX, DOCX, XLSX, images, audio, HTML, CSV, JSON, XML) to Markdown for text analysis.

## Usage

Convert a file and save to output:
```bash
markitdown input_file.pdf -o output_file.md
```

Convert a file to stdout:
```bash
markitdown data.xlsx
```

Pipe stdin:
```bash
cat document.docx | markitdown -x docx > document.md
```
