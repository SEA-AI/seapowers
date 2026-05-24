# /// script
# dependencies = ["tiktoken"]
# ///
"""Count tokens in markdown files using tiktoken.

For files with YAML frontmatter (--- delimiters), counts only the body.
For all other files, counts the full content.

Usage: uv run count_tokens.py <file1> [file2 ...]
Output: one token count per line, in the same order as the input files.
"""
import sys
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

for path in sys.argv[1:]:
    text = open(path).read()
    parts = text.split("---\n", 2)
    content = parts[2] if len(parts) >= 3 and text.startswith("---") else text
    print(len(enc.encode(content)))
