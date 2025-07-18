from neo4j import GraphDatabase

# Connection to Neo4j
uri = "bolt://localhost:7687"  # If you're using Neo4j Desktop
username = "neo4j"
password = "namanmathura"

driver = GraphDatabase.driver(uri, auth=(username, password))

def close_driver():
    driver.close()
