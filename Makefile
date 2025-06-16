# QA Generator with Human Review

# Variables
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Default target
.PHONY: help
help:
	@echo "QA Generator with Human Review"
	@echo ""
	@echo "Setup:"
	@echo "  make setup              - Install dependencies"
	@echo ""
	@echo "Generate & Review:"
	@echo "  make qa-pairs           - Generate QA pairs from data/txt/"
	@echo "  make export-labelstudio - Export for Label Studio review"
	@echo "  make start-labelstudio  - Start Label Studio server"
	@echo "  make process-reviews    - Process review results (EXPORT_FILE=path/to/export.json)"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean              - Remove generated files"
	@echo "  make stats              - Show generation statistics"

# Setup dependencies
.PHONY: setup
setup:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	mkdir -p data/{txt,generated,labelstudio,reviewed} configs
	@echo "✓ Setup complete. Copy configs/config.example.yaml to configs/config.yaml"

# Convert pdfs to markdown
.PHONY: convert-pdfs
convert-pdfs:
	@echo "Converting PDFs to Markdown..."
	$(PYTHON) convert_pdfs.py
	@echo "✓ Conversion complete. Check data/txt/ for markdown files."


# Generate QA pairs with source references
.PHONY: qa-pairs
qa-pairs:
	@echo "Generating QA pairs with source references..."
	$(PYTHON) generate_qa.py

# Filter generated QA pairs
.PHONY: filter-qa-pairs
filter-qa-pairs:
	@echo "Filtering generated QA pairs..."
	$(PYTHON) filter_qa_pairs.py
	@echo "✓ Filtering complete. Check data/filtered for filtered QA pairs."

# Clean generated files
.PHONY: clean
clean:
	rm -rf data/generated/* data/labelstudio/* data/reviewed/* data/review/* data/filtered/* data/rejected/*
	@echo "✓ Cleaned generated files"


# Export to Label Studio
.PHONY: export-labelstudio
export-labelstudio:
	@echo "Exporting QA pairs to Label Studio format..."
	$(PYTHON) export_to_labelstudio.py

# Start Label Studio
.PHONY: start-labelstudio
start-labelstudio:
	$(VENV)/bin/label-studio start

# Process review results
.PHONY: process-reviews
process-reviews:
	@if [ -z "$(EXPORT_FILE)" ]; then \
		echo "Usage: make process-reviews EXPORT_FILE=path/to/export.json"; \
		exit 1; \
	fi
	$(PYTHON) process_labelstudio_results.py "$(EXPORT_FILE)"

# Show statistics
.PHONY: stats
stats:
	@echo "Statistics:"
	@echo "- Input files: $$(ls -1 data/txt/*.txt 2>/dev/null | wc -l)"
	@echo "- Generated QA files: $$(ls -1 data/generated/*.json 2>/dev/null | wc -l)"
	@echo "- Reviewed files: $$(ls -1 data/reviewed/*.json 2>/dev/null | wc -l)"