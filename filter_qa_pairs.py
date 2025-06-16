import argparse
import json
import os
from pathlib import Path

import yaml
from datasets import Dataset
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas import evaluate

with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize OpenAI client
api_key = config['api-endpoint']['api_key']
os.environ["OPENAI_API_KEY"] = api_key


def main():
    parser = argparse.ArgumentParser(description="Filter QA pairs based on criteria")
    parser.add_argument(
        "--input_dir",
        type=str,
        default="data/generated",
        help="Directory containing the input JSON files with QA pairs",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/filtered",
        help="Directory to save the filtered QA pairs",
    )
    parser.add_argument(
        "--rejected_dir",
        type=str,
        default="data/rejected",
        help="Directory to save the rejected QA pairs",
    )
    parser.add_argument(
        "--faithfulness_threshold",
        type=float,
        default=0.9,
        help="Minimum faithfulness score to keep a QA pair",
    )
    parser.add_argument(
        "--answer_relevancy_threshold",
        type=float,
        default=0.8,
        help="Minimum answer relevance score to keep a QA pair",
    )
    parser.add_argument(
        "--context_precision_threshold",
        type=float,
        default=0.8,
        help="Minimum context precision score to keep a QA pair",
    )
    parser.add_argument(
        "--context_recall_threshold",
        type=float,
        default=0.8,
        help="Minimum context recall score to keep a QA pair",
    )
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    rejected_dir = Path(args.rejected_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)

    for input_file in input_dir.glob("*.json"):
        print(f"Processing {input_file.name}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)

        filtered_pairs = []
        rejected_pairs = []
        # save contexts for context precision computation
        contexts = [qa_pair["reference"]["chunk_text"] for qa_pair in qa_pairs]
        for qa_pair in qa_pairs:
            question = qa_pair["question"]
            answer = qa_pair["answer"]
            context = qa_pair["reference"]["chunk_text"]
            data_sample = {
                "question": [question],
                "answer": [answer],
                "contexts": [[context]],
                "ground_truth": [answer]
            }
            metrics = {}
            score = evaluate(Dataset.from_dict(data_sample), metrics=[faithfulness, answer_relevancy, context_recall])
            metrics["faithfulness"] = score["faithfulness"][0]
            metrics["answer_relevancy"] = score["answer_relevancy"][0]
            metrics["context_recall"] = score["context_recall"][0]
            # compute context precision
            data_sample["contexts"] = [contexts]
            score = evaluate(Dataset.from_dict(data_sample), metrics=[context_precision])
            metrics["context_precision"] = score["context_precision"][0]
            # save metrics
            qa_pair["metrics"] = metrics

            if (metrics["faithfulness"] >= args.faithfulness_threshold and
                metrics["answer_relevancy"] >= args.answer_relevancy_threshold and
                metrics["context_precision"] >= args.context_precision_threshold and
                metrics["context_recall"] >= args.context_recall_threshold):

                filtered_pairs.append(qa_pair)
            else:
                print(f"Rejected pair: {qa_pair['question']} -> {qa_pair['answer']}")
                rejected_pairs.append(qa_pair)


        output_file = output_dir / input_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_pairs, f, indent=2, ensure_ascii=False)

        rejected_file = rejected_dir / input_file.name
        with open(rejected_file, 'w', encoding='utf-8') as f:
            json.dump(rejected_pairs, f, indent=2, ensure_ascii=False)

        print(f"Filtered pairs saved to {output_file}")


if __name__ == "__main__":
    main()
