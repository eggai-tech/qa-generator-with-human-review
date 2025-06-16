# QA Generator with Human Review

Generate QA pairs from documents with human review workflow via [Label Studio](https://github.com/HumanSignal/label-studio/). Includes source tracking and quality filtering for creating ground truth evaluation datasets.

## Features

- Generate QA pairs with source references (line numbers, chunks)
- Human review interface using Label Studio
- Quality filtering based on review scores
- Multiple export formats

## Prerequisites

- Python 3.10+
- An LLM provider API key (OpenAI, Anthropic, etc.) or local LLM (vLLM, Ollama)
- macOS/Linux (Windows users may need WSL)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone git@github.com:eggai-tech/qa-generator-with-human-review.git
cd qa-generator-with-human-review

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make setup
```

### 2. Configure Your LLM Provider

Copy the example config and add your API key:

```bash
cp configs/config.example.yaml configs/config.yaml
```

Then edit `configs/config.yaml` and configure your API key:

```yaml
api-endpoint:
  api_key: "your-api-key-here"
```

### 3. Prepare Your Documents

Place your text documents in the `data/txt/` directory or alternatively if you have PDFs, place them in `data/pdf/` and run the conversion to markdown:

```bash
make convert-pdfs
```

### 4. Generate QA Pairs

```bash
make qa-pairs
```
This will process all the documents in `data/txt` and save the generated QA pairs as json files in `data/generated`

### 5. Filter QA Pairs based on Quality metrics

```bash
make filter-qa-pairs
```

This will filter the generated QA pairs based on quality metrics [faithfulness, answer relevance, context accuracy, context recall](https://docs.ragas.io/en/v0.1.21/concepts/metrics/) and save the filtered pairs in `data/filtered`.


## Human Review Process

```bash
# 1. Export QA pairs for review
make export-labelstudio

# 2. Start Label Studio
make start-labelstudio

# 3. In Label Studio (http://localhost:8080):
#    - Create project "QA Pairs Review"
#    - Import label_config.xml and qa_review_tasks.json
#    - Review QA pairs (rate accuracy, relevance, quality)

# 4. Process review results
make process-reviews EXPORT_FILE=path/to/export.json
```


## Commands

```bash
make setup              # Initial setup
make qa-pairs           # Generate QA pairs
make filter-qa-pairs    # Filter QA pairs based on quality
make export-labelstudio # Export for review
make start-labelstudio  # Start Label Studio
make process-reviews EXPORT_FILE=<file>  # Process results
```

## Configuration

Edit `configs/config.yaml` to customize:

```yaml
llm:
  provider: "api-endpoint"  # or "vllm", "ollama", etc.

api-endpoint:
  api_base: "https://api.openai.com/v1"
  api_key: "your-key-here"
  model: "gpt-4o-mini"  # Model depends on provider

generation:
  temperature: 0.7
  chunk_size: 2000
  num_pairs: 5  # QA pairs per chunk
```


## Troubleshooting

- **Label Studio won't start**: Try `venv/bin/label-studio start --port 8081`
- **LLM errors**: Check API key in `configs/config.yaml`
- **Large documents**: Reduce `chunk_size` in config


## Example Output

```json
{
  "question": "What is the issue price of the EUR 15,000,000 Floating Rate Preferred Senior Notes?",
  "answer": "The issue price is 100 per cent free to trade.",
  "reference": {
    "chunk_id": 0,
    "line_start": 1,
    "line_end": 45,
    "source_document": "DE000DDA0NU1.pdf.txt"
  }
}
```

## License

MIT

## Acknowledgments

- Uses [Label Studio](https://labelstud.io/) for human review interface
- Supports multiple LLM providers (OpenAI, Anthropic, local models)