---
name: repomix
description: Pack entire codebase or directory into a single optimized Markdown/XML file for LLM context ingestion.
---

# Repomix

Package your repository into a single AI-friendly file.

## Usage

- Pack current directory to `repomix-output.md`:
  `npx repomix`

- Pack with custom output path:
  `npx repomix --output custom-output.xml`

- Compress and exclude node_modules / build dirs automatically.
