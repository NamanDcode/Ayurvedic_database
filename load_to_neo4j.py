import pandas as pd
from neo4j_connection import driver

# Load Excel
df = pd.read_excel("data.xlsx")

# Clean the AF-Ingredient Table
af_ingredient_df = df[['Table 2. AF-Ingredients data', 'Unnamed: 5']].dropna()
af_ingredient_df.columns = ['Formulation', 'Ingredient']
af_ingredient_df = af_ingredient_df[af_ingredient_df['Formulation'] != 'AF']
af_ingredient_df['Ingredient'] = af_ingredient_df['Ingredient'].astype(str).str.strip().str.lower()

def load_data(tx, formulation, ingredient):
    tx.run("""
        MERGE (f:Formulation {name: $formulation})
        MERGE (i:Ingredient {name: $ingredient})
        MERGE (f)-[:CONTAINS]->(i)
    """, formulation=formulation, ingredient=ingredient)

with driver.session() as session:
    for index, row in af_ingredient_df.iterrows():
        session.write_transaction(load_data, row['Formulation'], row['Ingredient'])

print("Data loaded into Neo4j successfully.")
