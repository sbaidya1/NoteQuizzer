"""
Utility functions for PDF processing, chunking, embedding, and storage

Includes:
- Extracting text from PDFs using PyMuPDF
- Splitting documents into chunks for embedding
- Removing duplicate chunks
- Storing and persisting chunks in ChromaDB
- Clearing all stored data (ChromaDB, DB records, and uploaded files)
"""

import os, uuid, fitz, shutil
from uuid import uuid4

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from . import db
from .models import File

# embedding model used for chunk representation
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

# path to persist ChromaDB data
CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'chroma_db')
)

# extracts raw text from all pages in the PDF using PyMuPDF
def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text()
    return text

# loads and splits pdf into text chunks
# adds unique chunk ID and source filename to each chunk's metadata
def load_and_split_pdf(filepath):
    loader = PyMuPDFLoader(filepath)
    documents = loader.load()

    # splits pdf into chunks of 300 characters with overlap of 50 characters
    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    unique_chunks = []
    seen = set()
    for doc in split_docs:
        doc_content = doc.page_content.strip()

        # ensures chunks are unique + adds metadata
        if doc_content not in seen:
            doc.metadata["chunk_id"] = str(uuid.uuid4())[:8]
            doc.metadata["source"] = os.path.basename(filepath)
            unique_chunks.append(doc)
            seen.add(doc_content)

    return unique_chunks

# stores chunks in a persistent ChromaDB vector store
def store_chunks_in_chromadb(chunks):
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    vectorstore.persist()

# Completely clears chroma vectore store, sqlalchemy db, and uploads folder 
def clear_all_data(upload_folder):
    # clear chroma 
    if os.path.exists(CHROMA_DB_PATH):
        shutil.rmtree(CHROMA_DB_PATH)

    # clear sql db
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    # clear uploads folder
    for f in os.listdir(upload_folder):
        os.remove(os.path.join(upload_folder, f))
