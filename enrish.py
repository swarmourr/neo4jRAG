"""
This is an extension of the main base code to use the Together API to enrich a Neo4j database with movie information.
This code demonstrates how to use the Together API to generate responses for enriching a Neo4j database with movie information.
"""

import os
import streamlit as st
from neo4j import GraphDatabase
from together import Together

# Neo4j connection details
uri = "bolt://localhost:7687"
user = "neo4j"
password = "your_password_here"

# Initialize the Neo4j driver
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

def retrieve_information():
    query = """
    MATCH (m:Movie)
    RETURN m.title AS title, m.tagline AS tagline, m.released AS released
    LIMIT 30
    """
    
    with driver.session() as session:
        results = session.read_transaction(query_neo4j, query)
    
    if results:
        return "\n".join([f"Title: {r['title']}, Tagline: {r['tagline']}, Released: {r['released']}" for r in results])
    else:
        return "No movies found in the database."

def create_prompt(retrieved_info, user_query):
    prompt = f"Based on the following movie information:\n{retrieved_info}\n\nAnswer the question: {user_query}\n\nIf applicable, provide suggestions to add or update information in the database in the following format:\n- Add movie: Title, Tagline, Released\n- Update movie: Title, Tagline, Released"
    return prompt

def generate_response(prompt):
    try:
        stream = client.chat.completions.create(
            model="meta-llama/Llama-2-70b-chat-hf",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=300,
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

def parse_enrichment_suggestions(response_text):
    suggestions = []
    lines = response_text.split('\n')
    for line in lines:
        if "Add movie:" in line or "Update movie:" in line:
            suggestions.append(line)
    return suggestions

def enrich_database(suggestions):
    try:
        for suggestion in suggestions:
            if "Add movie:" in suggestion:
                parts = suggestion.split(":")[1:]
                title = parts[0].strip()
                tagline = parts[1].strip() if len(parts) > 1 else ""
                released = parts[2].strip() if len(parts) > 2 else ""

                query = """
                MERGE (m:Movie {title: $title})
                SET m.tagline = $tagline, m.released = $released
                RETURN m
                """
                with driver.session() as session:
                    session.write_transaction(query_neo4j, query, {"title": title, "tagline": tagline, "released": released})
                st.success(f"Added movie: {title}")

            elif "Update movie:" in suggestion:
                parts = suggestion.split(":")[1:]
                title = parts[0].strip()
                tagline = parts[1].strip() if len(parts) > 1 else ""
                released = parts[2].strip() if len(parts) > 2 else ""

                query = """
                MATCH (m:Movie {title: $title})
                SET m.tagline = $tagline, m.released = $released
                RETURN m
                """
                with driver.session() as session:
                    session.write_transaction(query_neo4j, query, {"title": title, "tagline": tagline, "released": released})
                st.success(f"Updated movie: {title}")

    except Exception as e:
        st.error(f"Error enriching database: {str(e)}")

# Streamlit UI
st.title("Movie Knowledge Integration")

user_input = st.text_input("Ask me anything about movies:")

if st.button("Retrieve Information"):
    retrieved_info = retrieve_information()
    
    if retrieved_info == "No movies found in the database.":
        st.warning(retrieved_info)
    else:
        st.subheader("Retrieved Information:")
        st.write(retrieved_info)
        st.session_state.retrieved_info = retrieved_info

if st.button("Generate Response"):
    if 'retrieved_info' not in st.session_state:
        st.warning("Please retrieve information first.")
    else:
        prompt = create_prompt(st.session_state.retrieved_info, user_input)
        st.write(f"Generated prompt: {prompt}")
        
        st.subheader("Generated Response:")
        response_placeholder = st.empty()
        full_response = ""
        for token in generate_response(prompt):
            full_response += token
            response_placeholder.markdown(full_response + "▌")
        response_placeholder.markdown(full_response)

        # Store response in session state for review
        st.session_state.generated_response = full_response

if st.button("Enrich Database"):
    if 'generated_response' not in st.session_state:
        st.warning("Please generate a response first.")
    else:
        suggestions = parse_enrichment_suggestions(st.session_state.generated_response)
        if not suggestions:
            st.warning("No valid enrichment suggestions found.")
        else:
            st.subheader("Enrichment Suggestions:")
            st.write("\n".join(suggestions))
            if st.button("Confirm Enrichment"):
                enrich_database(suggestions)
                st.success("Database enriched successfully.")

# Close the Neo4j driver connection when the app is done
driver.close()
