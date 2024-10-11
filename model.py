import streamlit as st
from neo4j import GraphDatabase
from transformers import pipeline

# Neo4j connection details
uri = "bolt://neo4j:7687"
user = "neo4j"
password = "your_password_here"

driver = GraphDatabase.driver(uri, auth=(user, password))

# Initialize the text generation pipeline
generator = pipeline('text-generation', model='distilgpt2')

def query_neo4j(tx, query):
    result = tx.run(query)
    return [record for record in result]

def generate_response(prompt):
    response = generator(prompt, max_length=100, num_return_sequences=1)
    return response[0]['generated_text']

# Streamlit UI
st.title("Neo4j and LLM Integration")

# Display all movies in the database
if st.button("Show Movies"):
    with driver.session() as session:
        movies = session.read_transaction(query_neo4j, """
        MATCH (m:Movie)
        RETURN m.title AS title, m.tagline AS tagline, m.released AS released
        LIMIT 10
        """)
        
        prompt = "I have the following movies in my database:\n"
        for movie in movies:
            st.write(f"Title: {movie['title']}, Tagline: {movie['tagline']}, Released: {movie['released']}")
            prompt += f"Title: {movie['title']}, Tagline: {movie['tagline']}, Released: {movie['released']}\n"
        prompt += "\nCan you summarize these movies?"

        # Generate and display summary
        if st.button("Generate Summary"):
            summary = generate_response(prompt)
            st.write("Summary:", summary)

# Query input and result display
query = st.text_area("Enter a Cypher query:")
if st.button("Run Query"):
    with driver.session() as session:
        result = session.read_transaction(query_neo4j, query)
        st.write(result)

driver.close()
