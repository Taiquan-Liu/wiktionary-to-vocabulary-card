# File Manager Module

The `file_manager.py` module implements intelligent wordcard handling across learning stages for the Wiktionary Vocabulary Card project.

## Features

### 🔍 **File Discovery**
- Searches for existing wordcards across New, Memorizing, and Remembered folders
- Supports exact and case-insensitive filename matching
- Returns both file path and current learning stage

### 📖 **Content Analysis**
- Parses existing markdown wordcard files
- Extracts tags, URLs, custom text, word sections, and articles
- Handles the existing ad-note format for conjugation tables and definitions

### 🎯 **Stage Management**
Implements intelligent rules for wordcard placement:
- **New wordcards** → Created in `New` folder
- **Existing in New/Memorizing** → Kept in same location
- **Existing in Remembered** → Moved back to `Memorizing` folder

### 🔄 **Article Field Transformation**
- Converts `custom_text` fields to `article` format
- Appends new article content to existing articles
- Maintains article history across updates

## Usage

### Basic Usage

```python
from wiktionary_vocab_card.file_manager import FileManager

# Initialize with default configuration
manager = FileManager()

# Process a wordcard with intelligent handling
final_path, was_moved = manager.process_wordcard(
    word="example",
    new_content=wordcard_content,
    new_article="article content #tag ([web](url), [[local]])"
)
```

### Individual Functions

```python
from wiktionary_vocab_card.file_manager import (
    find_existing_wordcard,
    parse_existing_wordcard,
    append_article_content,
    determine_target_location,
    save_wordcard
)

# Find existing wordcard
result = find_existing_wordcard("word")
if result:
    filepath, stage = result

# Parse existing content
content = parse_existing_wordcard(filepath)

# Append article content
updated_content = append_article_content(content, "new article")

# Determine target location
target_path, target_stage = determine_target_location("word", current_stage)

# Save wordcard
success = save_wordcard(content, target_path)
```

### Configuration

The module uses the enhanced configuration system from `config.py`:

```yaml
vault:
  path: "/path/to/obsidian/vault"
  learning_stages:
    new: "New"
    memorizing: "Memorizing"
    remembered: "Remembered"

file_management:
  check_existing: true      # Enable intelligent wordcard discovery
  append_articles: true     # Append new articles to existing wordcards
  move_from_remembered: true # Move wordcards from Remembered to Memorizing

output:
  create_directories: true  # Create directories if they don't exist
  backup_existing: false    # Backup existing files before overwriting
```

## Integration with Existing Code

The FileManager integrates seamlessly with the existing codebase:

### With MarkdownGenerator

```python
from wiktionary_vocab_card.generator import MarkdownGenerator
from wiktionary_vocab_card.file_manager import FileManager

# Generate wordcard content
generator = MarkdownGenerator(parser, content, config)
markdown_content = generator.generate_card()

# Convert to structured format for FileManager
structured_content = {
    'word': content['word'],
    'tags': content['word_types'] + content['kotus_types'],
    'url': parser.url,
    'custom_text': config.get('custom_text', ''),
    'word_sections': [...],  # Structured sections
    'articles': []
}

# Process with intelligent handling
manager = FileManager(config)
final_path, was_moved = manager.process_wordcard(
    word=content['word'],
    new_content=structured_content,
    new_article="new article content"
)
```

## File Format

The module maintains compatibility with the existing markdown format:

```markdown

#noun #kala
https://en.wiktionary.org/wiki/word
# noun
```ad-note
title: Conjugation Table
collapse: collapse
[conjugation table content]
```
```ad-note
title: Definition
collapse: collapse
[definition content]
```
# Articles
- article - content #tag ([web](url), [[local]])
```

## Error Handling

The module includes comprehensive error handling:
- Graceful handling of missing vault configuration
- Safe file operations with proper exception handling
- Logging for debugging and monitoring
- Validation of file paths and content

## Testing

Run the test suite to verify functionality:

```bash
# Basic functionality tests
python test_file_manager.py

# Integration examples
python integration_example.py
```

## Key Functions

### `FileManager.process_wordcard(word, new_content, new_article)`
Main entry point that orchestrates the entire workflow:
1. Find existing wordcard
2. Parse existing content if found
3. Append new article content
4. Determine target location based on stage rules
5. Save wordcard with merged content

### `FileManager.find_existing_wordcard(word)`
Search across all stage directories for existing wordcards.

### `FileManager.parse_existing_wordcard(filepath)`
Extract structured content from existing markdown files.

### `FileManager.append_article_content(existing_content, new_article)`
Merge new article content with existing wordcard content.

### `FileManager.determine_target_location(word, existing_location)`
Apply stage management rules to determine target location.

### `FileManager.save_wordcard(content, target_path)`
Write wordcard content to file with directory creation.

## Benefits

- **Intelligent Discovery**: Automatically finds existing wordcards across learning stages
- **Content Preservation**: Merges new content with existing while preserving structure
- **Stage Management**: Implements learning progression rules automatically
- **Safe Operations**: Creates directories and handles errors gracefully
- **Backward Compatible**: Works with existing markdown format and configuration
- **Flexible**: Can be used as individual functions or as a complete workflow