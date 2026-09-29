---
name: aider
description: AI pair programming in terminal - automatically edit code, run tests, and manage git commits based on instructions.
---

# Aider AI Pair Programmer

Run AI pair programming session directly in your terminal attached to your git repository.

## Usage

- Start Aider with specific files:
  `aider main.py utils.py`

- Use with specific model:
  `aider --model sonnet`

- Automatically run tests on edit:
  `aider --test-cmd "pytest"`
