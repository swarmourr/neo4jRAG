# Movie Knowledge Graph with LLM

This project is an interactive web application that combines Neo4j, a powerful graph database, and a Large Language Model (LLM), accessed via the Together API. The application allows users to query a movie database and receive AI-generated responses based on the data retrieved from the graph database.

## Objectives

- Understand how to connect and query a Neo4j database.
- Learn to use Streamlit to create an interactive web application.
- Integrate an LLM using the Together API to generate natural language responses.
- Implement Retrieval-Augmented Generation (RAG) by combining real-time data retrieval and language model generation.

## Prerequisites

Before starting, ensure you have the following:

- Neo4j Database: Installed and running locally or via Docker with a movie dataset.
- Streamlit: Installed in your Python environment.
- Together API Key: Sign up at [Together](https://together.ai) to get an API key.
- Python Packages: Install the necessary packages using the following command:
  ```
  pip install neo4j streamlit together-ai
  ```
- Python Environment: Ensure you are using Python 3.7 or higher.

## Step-by-Step Guide

### Step 0: Obtain Together.ai API Token

To get the API key from Together.ai, follow these steps:

1. Sign in to your Together.ai account.
2. Navigate to Settings and select API Keys.
3. Copy the API key and store it securely.

### Step 1: Set Up Neo4j with Docker

1. Create a Dockerfile to define the Neo4j environment:
   ```dockerfile
   FROM neo4j
   ENV NEO4J_AUTH=neo4j/your_password_here
   EXPOSE 7474 7687
   ```

2. Build and run the Neo4j container:
   ```bash
   docker build -t my-neo4j-image .
   docker run -d --name my-neo4j-container -p 7474:7474 -p 7687:7687 my-neo4j-image
   ```

3. Access the Neo4j browser at http://localhost:7474 and log in using the credentials.

4. Import the movie dataset using Cypher queries from `data.cypher`:
   ```bash
   cat data.cypher | cypher-shell -u neo4j -p your_password
   ```

### Step 2: Build the Streamlit Application

1. Create the main app in `app.py`:
   ```python
   import os
   import streamlit as st
   from neo4j import GraphDatabase
   from together import Together

   uri = "bolt://localhost:7687"
   user = "neo4j"
   password = "your_password_here"
   driver = GraphDatabase.driver(uri, auth=(user, password))
   client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

   def query_neo4j(tx, query, params=None):
       result = tx.run(query, params or {})
       return [record for record in result]

   def retrieve_information():
       query = """
       MATCH (m:Movie)
       RETURN m.title AS title, m.tagline AS tagline, m.released AS released
       LIMIT 30
       """
       with driver.session() as session:
           return session.read_transaction(query_neo4j, query)

   def create_prompt(retrieved_info, user_query):
       return f"Based on the following movie information:\n{retrieved_info}\n\nAnswer the question: {user_query}"

   def generate_response(prompt):
       return client.chat.completions.create(
           model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
           messages=[{"role": "user", "content": prompt}]
       )

   def main():
       st.title("Movie Knowledge Graph with LLM")
       user_query = st.text_input("Enter your question:")
       if st.button("Submit"):
           retrieved_info = retrieve_information()
           prompt = create_prompt(retrieved_info, user_query)
           response = generate_response(prompt)
           st.write(response)

   if __name__ == "__main__":
       main()
   ```

2. Run the application:
   ```bash
   streamlit run app.py
   ```

### Step 3: Testing the API

1. Use `test_api.py` to test the Together API integration:
   ```python
   import os
   from together import Together

   client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

   def test_together_api():
       response = client.chat.completions.create(
           model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
           messages=[{"role": "user", "content": "Hello, LLM!"}]
       )
       print(response)

   if __name__ == "__main__":
       test_together_api()
   ```

2. Run the test:
   ```bash
   python test_api.py
   ```

## Project Structure

```
.
├── Dockerfile      # Docker setup for Neo4j
├── README.md       # Project documentation
├── app.py          # Main Streamlit application file
├── data.cypher     # Cypher file to import the movie dataset
├── ennoncer        # Additional module for processing
├── enrish.py       # Script for text enrichment
├── model.py        # Model definition and related logic
├── test_api.py     # Script for testing API integration
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.