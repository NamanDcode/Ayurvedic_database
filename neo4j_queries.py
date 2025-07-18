from neo4j_connection import driver

def get_formulation_ingredients(formulation_name):
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Formulation {name: $name})-[:CONTAINS]->(i:Ingredient)
            RETURN i.name AS ingredient
        """, name=formulation_name)
        return [record["ingredient"] for record in result]
