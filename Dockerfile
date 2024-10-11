# Use the official Neo4j image from the Docker Hub
FROM neo4j:latest

# Set environment variables for Neo4j
ENV NEO4J_AUTH=neo4j/your_password_here

# Expose the default Neo4j port
EXPOSE 7474 7687

# Commented out build and run commands
# docker build -t my-neo4j-image .
# docker run -d --name my-neo4j-container -p 7474:7474 -p 7687:7687 my-neo4j-image
