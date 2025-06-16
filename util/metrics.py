import openai
from langchain_core.vectorstores import InMemoryVectorStore, VectorStore
from sentence_transformers import SentenceTransformer, util

# Load a Sentence Transformer model for semantic similarity
embedding_model = SentenceTransformer("all-MiniLM-L12-v2")


# LLM-based completeness scoring function
def score_question_completeness(api_client, question, context=None, model="gpt-4o-mini"):

    prompt = f"""
You are an expert financial QA evaluator. Given a question (and optional context), assess how complete the question is.

A complete question:
- Clearly specifies the subject (e.g., company name, metric)
- Contains a time frame if relevant (e.g., “Q1 2023”)
- Is unambiguous and answerable without additional assumptions

An incomplete question:
- Lacks specificity (e.g., "What is the revenue?")
- Uses vague terms (e.g., "mentioned in the document", "discussed in the text", "according to the document", "mentioned in the summary")

Please rate the question from 1 (very incomplete) to 5 (fully complete), and briefly explain your reasoning.

Question: {question}
{f"Context: {context}" if context else ""}

Output format:
Score: <1–5>
Explanation: <short justification>
"""

    response = api_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a financial QA expert evaluating question completeness."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    output = response.choices[0].message.content
    lines = output.strip().split("\n")

    score_line = next((line for line in lines if line.lower().startswith("score")), None)
    explanation_line = next((line for line in lines if line.lower().startswith("explanation")), None)

    score = int(score_line.split(":")[1].strip()) if score_line else None
    explanation = explanation_line.split(":", 1)[1].strip() if explanation_line else None

    return {
        "completeness_score": score,
        "completeness_explanation": explanation,
        "is_complete": score >= 4
    }


# Relevance scoring function using embeddings
def check_question_relevance(question, context, threshold=0.65):
    """Check if a question is relevant to a given context using semantic similarity."""
    embeddings = embedding_model.encode([question, context], convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()

    return {
        "similarity_score": similarity,
        "is_relevant": similarity >= threshold
    }


def check_query_retrievability(question: str, vector_store: VectorStore, context: str, k: int = 5):
    """ Check if a question retrieves a specific context from the vector store."""
    results = vector_store.similarity_search(query=question, k=k)
    for doc in results:
        if context in doc.page_content:
            return True
    return False
