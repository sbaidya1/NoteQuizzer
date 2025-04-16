# NoteQuizzer - Quiz yourself with the content from your notes/readings!

NoteQuizzer is a Flask-based web app that lets you upload your PDF class notes or readings, then quiz yourself on a specific topic using AI. It uses semantic search and large language models to generate relevant quiz questions and evaluate your answers — giving you instant feedback and insights based on your own materials.

### 1. Upload your notes
<img src="demo_screenshots/upload_notes.png" width="400"/>

### 2. Set a topic and complete your quiz   
<img src="demo_screenshots/complete_quiz.png" width="400"/>

### 3. View your results   
<img src="demo_screenshots/quiz_eval.png" width="400"/>

## Features:

- Upload PDF notes/readings 
- Automatically chunks your content for vector-based semantic search
- Generates AI-powered quiz questions based on specific topics
- Scores answers and gives an explanation using natural language comparison
- Shows the relevant text (with file name and page number) for each question 

## Tech Stack:

- Flask – web framework
- SQLAlchemy – database management
- LangChain – LLM orchestration
- OpenAI GPT-4o – question generation and answer scoring
- HuggingFace Embeddings – text vectorization
- ChromaDB – local vector store
- PyMuPDF – PDF text extraction

## To run locally:

1. Clone the repo  
2. Create a virtual environment  
3. Install dependencies from `requirements.txt`  
4. Create a `.env` file using `.env.example`, and add your own OpenAI API key
5. Run the app with `python run.py`
