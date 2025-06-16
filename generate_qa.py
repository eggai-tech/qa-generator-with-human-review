#!/usr/bin/env python3
"""
Generate QA pairs with source references (chunk location and character positions)
"""
import json
from pathlib import Path
from typing import Dict, Any

from openai import OpenAI
import yaml
from tqdm import tqdm

# Load configuration
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize OpenAI client
api_config = config['api-endpoint']
client = OpenAI(
    api_key=api_config['api_key'],
    base_url=api_config['api_base']
)

def read_document(file_path):
    """Read document content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_text_with_positions(text, chunk_size=None, overlap=200, source_document=None):
    """Split text into overlapping chunks with position tracking"""
    # Use chunk_size from config if not specified
    if chunk_size is None:
        chunk_size = config.get('generation', {}).get('chunk_size', 2000)
        
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text = text[start:end]
        
        # Find line numbers for this chunk
        lines_before = text[:start].count('\n')
        lines_in_chunk = chunk_text.count('\n')
        
        chunk_data = {
            'id': chunk_id,
            'text': chunk_text,
            'char_start': start,
            'char_end': end,
            'line_start': lines_before + 1,
            'line_end': lines_before + lines_in_chunk + 1,
            'preview': chunk_text[:100].replace('\n', ' ') + '...'
        }
        
        if source_document:
            chunk_data['source_document'] = source_document
            
        chunks.append(chunk_data)
        
        chunk_id += 1
        start = end - overlap if end < len(text) else end
    
    return chunks

def find_answer_location(answer, chunk_text):
    """Try to find the approximate location of the answer in the chunk"""
    # Clean the answer for searching
    answer_words = answer.lower().split()[:5]  # First 5 words
    search_text = ' '.join(answer_words)
    
    # Try to find in chunk
    chunk_lower = chunk_text.lower()
    pos = chunk_lower.find(search_text)
    
    if pos != -1:
        # Find the line number within chunk
        lines_before = chunk_text[:pos].count('\n')
        return lines_before
    
    return None

def generate_qa_pairs_with_refs(chunk_data, prompt, num_pairs=None):
    """Generate QA pairs from a text chunk with references"""
    chunk_text = chunk_data['text']
    
    # Use num_pairs from config if not specified
    if num_pairs is None:
        num_pairs = config.get('generation', {}).get('num_pairs', 5)
    
    prompt = prompt.format(
        chunk_text=chunk_text,
        num_pairs=num_pairs
    )

    try:
        response = client.chat.completions.create(
            model=api_config['model'],
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates high-quality question-answer pairs for training data. Try to use direct quotes from the text when possible."},
                {"role": "user", "content": prompt}
            ],
            temperature=config.get('generation', {}).get('temperature', 0.7)
        )
        
        # Parse the response
        content = response.choices[0].message.content
        
        # Extract JSON from markdown code blocks if present
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        # Parse JSON and add references
        qa_pairs = json.loads(content)
        
        # Add reference information to each QA pair
        for qa in qa_pairs:
            qa['reference'] = {
                'chunk_id': chunk_data['id'],
                'char_start': chunk_data['char_start'],
                'char_end': chunk_data['char_end'],
                'line_start': chunk_data['line_start'],
                'line_end': chunk_data['line_end'],
                'chunk_preview': chunk_data['preview'],
                'chunk_text': chunk_text,
                'source_document': chunk_data.get('source_document', '')
            }
            
            # Try to find more specific location for the answer
            answer_line = find_answer_location(qa['answer'], chunk_text)
            if answer_line is not None:
                qa['reference']['answer_line_in_chunk'] = answer_line
                qa['reference']['answer_line_in_doc'] = chunk_data['line_start'] + answer_line
        
        return qa_pairs
        
    except Exception as e:
        print(f"Error generating QA pairs: {e}")
        return []

def create_review_format(qa_pairs, output_base):
    """Create different review formats"""
    # Create review directory
    review_dir = Path("data/review")
    review_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. JSON format with full references
    with open(review_dir / f"{output_base}_with_refs.json", 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    
    # 2. CSV format for spreadsheet review
    import csv
    with open(review_dir / f"{output_base}_review.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID', 'Question', 'Answer', 'Quality (1-5)', 'Accuracy (Y/N)', 'Notes',
            'Chunk ID', 'Lines', 'Chunk Preview'
        ])
        
        for i, qa in enumerate(qa_pairs):
            ref = qa['reference']
            writer.writerow([
                i + 1,
                qa['question'],
                qa['answer'],
                '',  # Quality rating (to be filled by reviewer)
                '',  # Accuracy (to be filled by reviewer)
                '',  # Notes (to be filled by reviewer)
                ref['chunk_id'],
                f"{ref['line_start']}-{ref['line_end']}",
                ref['chunk_preview']
            ])
    
    # 3. Markdown format for easy reading
    with open(review_dir / f"{output_base}_review.md", 'w', encoding='utf-8') as f:
        f.write(f"# QA Pairs Review Document\n\n")
        f.write(f"Total QA pairs: {len(qa_pairs)}\n\n")
        
        for i, qa in enumerate(qa_pairs):
            ref = qa['reference']
            f.write(f"## QA Pair {i + 1}\n\n")
            f.write(f"**Question:** {qa['question']}\n\n")
            f.write(f"**Answer:** {qa['answer']}\n\n")
            f.write(f"**Source Reference:**\n")
            f.write(f"- Chunk ID: {ref['chunk_id']}\n")
            f.write(f"- Document lines: {ref['line_start']}-{ref['line_end']}\n")
            if 'answer_line_in_doc' in ref:
                f.write(f"- Answer approximately at line: {ref['answer_line_in_doc']}\n")
            f.write(f"- Chunk preview: *{ref['chunk_preview']}*\n\n")
            f.write("---\n\n")

def get_prompt(config: Dict[str, Any], prompt_name: str) -> str:
    """Get prompt by name"""
    prompts = config.get('prompts', {})
    if prompt_name not in prompts:
        raise ValueError(f"Prompt '{prompt_name}' not found in configuration")
    return prompts[prompt_name]

def main():
    input_dir = Path("data/txt")
    # load qa prompt from config
    prompt = get_prompt(config, "qa_generation_v2")
    print(f"Using prompt: {prompt}")
    for input_file in tqdm(list(input_dir.iterdir())):
        # Input and output paths
        output_base = Path(input_file).stem
        output_file = f"data/generated/{output_base}_qa_pairs_with_refs.json"

        # Store source document info
        source_doc_info = {
            "filename": Path(input_file).name,
            "path": input_file,
            "generated_from": str(Path(input_file).absolute())
        }

        # Ensure output directories exist
        Path("data/generated").mkdir(parents=True, exist_ok=True)

        print(f"Reading document from {input_file}...")
        text = read_document(input_file)
        print(f"Document length: {len(text)} characters, {text.count(chr(10))} lines")

        chunks = chunk_text_with_positions(text, source_document=source_doc_info["filename"])
        if len(chunks) == 0:
            print(f"No chunks generated from {input_file}. Skipping...")
            continue
        print(f"Split into {len(chunks)} chunks")

        all_qa_pairs = []

        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)} (lines {chunk['line_start']}-{chunk['line_end']})...")
            qa_pairs = generate_qa_pairs_with_refs(chunk, prompt)
            all_qa_pairs.extend(qa_pairs)
            print(f"  Generated {len(qa_pairs)} QA pairs")

        print(f"\nTotal QA pairs generated: {len(all_qa_pairs)}")

        # Save main output with references
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_qa_pairs, f, indent=2, ensure_ascii=False)

        print(f"Saved to {output_file}")

        # Create review formats
        create_review_format(all_qa_pairs, output_base)
        print(f"Created review files in data/review/")

        # Print summary statistics
        print("\nSummary:")
        print(f"- Total QA pairs: {len(all_qa_pairs)}")
        print(f"- Average QA pairs per chunk: {len(all_qa_pairs) / len(chunks):.1f}")
        print(f"- Review files created:")
        print(f"  - data/review/{output_base}_with_refs.json (JSON with full references)")
        print(f"  - data/review/{output_base}_review.csv (CSV for spreadsheet review)")
        print(f"  - data/review/{output_base}_review.md (Markdown for easy reading)")


if __name__ == "__main__":
    main()