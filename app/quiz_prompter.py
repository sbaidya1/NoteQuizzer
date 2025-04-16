"""
LLM-powered utilities for quiz generation and answer evaluation

Includes:
- Generating quiz questions (in JSON format) based on chunked PDF content
- Comparing user answers to correct answers using language model
- Returning scores and explanations for answers (in JSON format)
"""

import json, re, os
from uuid import uuid4
from langchain_openai import ChatOpenAI

# load API key from environment
api_key = os.getenv("OPENAI_API_KEY")

# initialize language model (GPT-4o)
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=api_key
)

# generates quiz questions from given document chunks
def generate_questions(chunks):
    # format each chunk with its id and content
    chunk_texts = [
        f"(Chunk ID: {doc.metadata['chunk_id']}) {doc.page_content}"
        for doc, _ in chunks
    ]
    combined_chunks = "\n\n".join(chunk_texts)

    # prompt asking model to generate 5 questions in JSON format
    prompt = f"""
    Based only on the following content, generate 5 quiz questions. For each question,
    include the chunk_id(s) where the answer can be found.

    Content:
    {combined_chunks}

    Respond in this JSON format:
    [
      {{
        "question": "...",
        "answer": "...",
        "chunk_ids": ["..."]
      }},
      ...
    ]
    """

    response_text = model.predict(prompt)

    # clean model response to remove surrounding ```json
    return re.sub(r"^```json\n|\n```$", "", response_text).strip()

# evaluates a user’s answer by comparing it to the correct answer
def generate_quiz_results(question, correct_answer, user_answer):
    # prompt asking for similarity score and explanation in JSON format
    prompt = f"""
        Compare the following answer (my answer) to the correct answer. 
        Give a similarity score out of 10 and a brief explanation.

        Question: {question}
        Correct Answer: {correct_answer}
        My Answer: {user_answer}

        Respond in this JSON format:
        {{
            "score": <score_out_of_10>,
            "explanation": "<short_reason>"
        }}
        """
    try:
        response_text = model.predict(prompt)
        # clean model response to remove surrounding ```json
        cleaned = re.sub(r"^```json\n|\n```$", "", response_text).strip()
        return json.loads(cleaned)
    except:
        # fallback if model output cannot be parsed
        return {"score": "N/A", "explanation": "Could not parse model response."}
