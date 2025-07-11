# Elasticsearch 9 Index Creation for Kitsune

This directory contains ES9-compatible JSON files for creating your Kitsune search indices in Kibana Console.

## Files

- `es9_kibana_console_commands.json` - Complete JSON with all commands
- `01_wikidocument_index.json` - WikiDocument index creation
- `02_questiondocument_index.json` - QuestionDocument index creation
- `03_forumdocument_index.json` - ForumDocument index creation
- `04_profiledocument_index.json` - ProfileDocument index creation
- `05_answerdocument_index.json` - AnswerDocument index creation
- `06_create_aliases.json` - Create all aliases
- `07_reindex_wikidocument.json` - Reindex WikiDocument from remote
- `08_reindex_questiondocument.json` - Reindex QuestionDocument from remote
- `09_reindex_forumdocument.json` - Reindex ForumDocument from remote
- `10_reindex_profiledocument.json` - Reindex ProfileDocument from remote
- `11_reindex_answerdocument.json` - Reindex AnswerDocument from remote

## Usage

### Step 1: Create Indices
1. Open Kibana Console (Dev Tools)
2. Copy and paste commands from files 01-05 to create indices
3. Execute each command one by one

### Step 2: Create Aliases
4. Copy and paste commands from file 06 to create aliases
5. Execute the alias commands

### Step 3: Reindex Data (Optional)
6. Copy and paste commands from files 07-11 to reindex data from remote
7. Execute each reindex command
8. Note: Reindexing runs asynchronously (`wait_for_completion=false`)

## Order of Operations

1. Create indices (01-05)
2. Create aliases (06)
3. Reindex data from remote (07-11) - Optional

## ES9 Compatibility

All configurations have been updated for Elasticsearch 9:
- Uses built-in tokenizers (no plugins required)
- CJK language support via `cjk_bigram` filter
- Updated analysis settings
- ES9 mapping syntax
- Removed deprecated settings

## Notes

- Index names include timestamp: `sumo_stage_*_20221128102837`
- Alias names remain clean: `sumo_stage_*_read` / `sumo_stage_*_write`
- All indices include multilingual support
- Analyzers optimized for search performance
- Reindex operations are asynchronous for large datasets