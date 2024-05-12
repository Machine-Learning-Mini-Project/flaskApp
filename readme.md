This is the Flask part of the application. It contains APIs for auto-grading using gpt4-turbo model and plagiarism check using cosine similarity.

Run in dev mode : `flask --app apps run --debug --port 5001`

.env
```bash
OPENAI_API_KEY= <openAi key>
LANGCHAIN_API_KEY= <Langchain API key>
LANGCHAIN_TRACING_V2=true
```
