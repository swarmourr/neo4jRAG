"""
This Streamlit application integrates with a Neo4j database and the Together API to provide movie-related information.
It performs the following tasks:
1. Connects to a Neo4j database to retrieve movie information.
2. Uses the Together API to generate responses based on the retrieved movie information and user queries.
3. Displays the retrieved information and generated responses in a Streamlit web interface.

Key components:
- Neo4j connection details and driver initialization.
- Functions to query Neo4j and retrieve movie information.
- Functions to create prompts and generate responses using the Together API.
- Streamlit UI for user interaction and displaying results.
"""

import os
import streamlit as st
from neo4j import GraphDatabase
from together import Together

# Neo4j connection details
uri = "bolt://localhost:7687"
user = "neo4j"
password = "your_password_here"

# Create a Neo4j driver instance
driver = GraphDatabase.driver(uri, auth=(user, password))

# Initialize the Together API client
client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))

def query_neo4j(tx, query, params=None):
    try:
        result = tx.run(query, params or {})
        return [record for record in result]
    except Exception as e:
        st.error(f"Neo4j query error: {str(e)}")
        return []

def retrieve_information(user_query):
    query = """
    MATCH (m:Movie)
    RETURN m.title AS title, m.tagline AS tagline, m.released AS released
    LIMIT 30
    """
    
    with driver.session() as session:
        results = session.read_transaction(query_neo4j, query)
        print(len(results))
    if results:
        return "\n".join([f"Title: {r['title']}, Tagline: {r['tagline']}, Released: {r['released']}" for r in results])
    else:
        return "No movies found in the database."

def create_prompt(retrieved_info, user_query):
    prompt = f"Based on the following movie information:\n{retrieved_info}\n\nAnswer the question: {user_query}"
    return prompt

def generate_response(prompt):
    try:
        stream = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=1000,
            temperature=0.1,
            top_p=0.9,
            top_k=50,
        )
        
        generated_text = ''
        for chunk in stream:
            if chunk.choices:
                content = chunk.choices[0].delta.content
                if content:
                    generated_text += content
                    yield content
        
        if not generated_text:
            yield "No response generated from the model."
    except Exception as e:
        yield f"Error with model: {str(e)}"

# Streamlit UI
st.title("Movie Knowledge Integration")

user_input = st.text_input("Ask me anything about movies:")

if st.button("Submit"):
    retrieved_info = retrieve_information(user_input)
    
    if retrieved_info == "No movies found in the database.":
        st.warning(retrieved_info)
    else:
        st.subheader("Retrieved Information:")
        #st.write(retrieved_info)
        
        prompt = create_prompt(retrieved_info, user_input)
        #st.write(f"Generated prompt: {prompt}")
        
        st.subheader("Generated Response:")
        response_placeholder = st.empty()
        full_response = ""
        for token in generate_response(prompt):
            full_response += token
            response_placeholder.markdown(full_response + "▌")
        response_placeholder.markdown(full_response)

# Close the Neo4j driver connection when the app is done
driver.close()
