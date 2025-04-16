"""
Flask route handlers for uploading PDFs, searching notes, generating quizzes, 
and evaluating user answers

Includes:
- Uploading and storing PDF files
- Chunking and embedding for semantic search
- Generating quiz questions from relevant chunks
- Evaluating user-submitted answers using a language model
- Resetting the system (clearing ChromaDB, database, and uploads)
"""

import os, json
from uuid import uuid4

from flask import current_app as app, render_template, request, redirect
from langchain_community.vectorstores import Chroma

from . import db
from .models import File
from .pdf_processor import extract_text_from_pdf, load_and_split_pdf, store_chunks_in_chromadb, clear_all_data, embeddings
from .quiz_prompter import generate_questions, generate_quiz_results

# temporary store for current quiz data
quiz_store = {}

# homepage; dislays all uploaded files  
@app.route('/')
def index():
    # gets all files from sqlachemy db 
    notes = File.query.all()
    return render_template('index.html', notes=notes)

# upload route; saves PDF to uploads folder + sql db, and creates + stores chunks in chroma
@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files') # all files uploaded
    for file in files: 
        if file and file.filename.endswith('.pdf'):
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
             
            # save file to upload folder
            file.save(filepath)

            # process and embed chunks
            chunks = load_and_split_pdf(filepath)
            store_chunks_in_chromadb(chunks)

            # extract text and save to sql db
            text = extract_text_from_pdf(filepath)
            db.session.add(File(filename=filename, content=text))
    db.session.commit()
    return redirect("/")

# search route; retrieves similar chunks and generates quiz questions based on topic
@app.route('/search', methods=['POST'])
def search():
    topic = request.form.get('topic')

    # perform semantic search for topic over chromadb, gets 12 closest results 
    vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)
    results = vectorstore.similarity_search_with_score(topic, k=12)

    #filter out less relevant results (similarity score > 1.6)
    filtered = [(doc, score) for doc, score in results if score <= 1.6]

    # map chunk id to relevant chunk data (to later be displayed to user)
    chunk_map = {
        doc.metadata['chunk_id']: {
            "text": doc.page_content,
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page", "unknown")
        }
        for doc, _ in filtered
    }

    # use LLM to generate quiz questions/answers based on filtered chunks (returns json format)
    qa_json = generate_questions(filtered)

    try:
        qa_list = json.loads(qa_json)

        # generate_questions() returns each question with its related chunk_ids
        # this block maps those chunk_ids to full chunk details (text, source, page)
        for qa in qa_list:
            qa["chunks"] = [
                {
                    "text": chunk_map.get(cid, {}).get("text", "[Missing Chunk]"),
                    "source": chunk_map.get(cid, {}).get("source", "unknown"),
                    "page": (chunk_map.get(cid, {}).get("page", 0) + 1) # add 1 so index starts at 1 not 0
                }
                for cid in qa.get("chunk_ids", [])
            ]
    except:
        qa_list = []

    # store quiz session using unique ID (used to retrieve quiz when evaluating answers)
    quiz_id = str(uuid4())
    quiz_store[quiz_id] = qa_list

    notes = File.query.all()
    return render_template("index.html", notes=notes, topic=topic, questions=qa_list, quiz_id=quiz_id)

# evaluation route; scores user answers against model answers
@app.route('/evaluate', methods=['POST'])
def evaluate():
    topic = request.form.get('topic')
    num_questions = int(request.form.get('num_questions', 0))
    quiz_id = request.form.get('quiz_id')

    # retrieve question/answers based on id
    qa_list = quiz_store.get(quiz_id, [])
    results = []

    for i in range(num_questions):
        q = request.form.get(f'question_{i}')
        a = request.form.get(f'answer_{i}') 
        ua = request.form.get(f'user_answer_{i}')
        # match current question to its relevant source chunks
        chunk_data = next((qa.get("chunks", []) for qa in qa_list if qa["question"] == q), [])

        # use LLM to evaluate how similar the user's answer is to the correct answer
        score_info = generate_quiz_results(q, a, ua)

        # store quiz evaluation results 
        results.append({
            "question": q,
            "correct_answer": a,
            "user_answer": ua,
            "score": score_info["score"],
            "explanation": score_info["explanation"],
            "chunks": chunk_data 
        })

    # remove quiz id (since done evaluating)
    quiz_store.pop(quiz_id, None)
    
    notes = File.query.all()
    return render_template("index.html", notes=notes, topic=topic, results=results)

# reset route; clears vectorstore, db, and uploaded files
@app.route('/reset', methods=['POST'])
def reset():
    clear_all_data(app.config['UPLOAD_FOLDER'])
    return redirect('/')
