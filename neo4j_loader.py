import pandas as pd
from neo4j import GraphDatabase

class HerbGraphLoader:
    def __init__(self):
        uri = "bolt://localhost:7687"
        user = "neo4j"
        password = "july1234"
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def _create_herb_pcm(self, tx, herb, pcm):
        tx.run("""
            MERGE (h:Herb {name: $herb})
            MERGE (p:PCM {name: $pcm})
            MERGE (h)-[:HAS_PCM]->(p)
        """, herb=herb, pcm=pcm)

    def _create_pcm_gene(self, tx, pcm, gene):
        tx.run("""
            MERGE (p:PCM {name: $pcm})
            MERGE (g:Gene {name: $gene})
            MERGE (p)-[:INTERACTS_WITH]->(g)
        """, pcm=pcm, gene=gene)

    def _create_gene_disease(self, tx, gene, disease):
        tx.run("""
            MERGE (g:Gene {name: $gene})
            MERGE (d:Disease {name: $disease})
            MERGE (g)-[:GENE_ASSOCIATED_WITH]->(d)
        """, gene=gene, disease=disease)

    def _create_gene_pathway(self, tx, gene, pathway):
        tx.run("""
            MERGE (g:Gene {name: $gene})
            MERGE (pw:Pathway {name: $pathway})
            MERGE (g)-[:GENE_INVOLVED_IN]->(pw)
        """, gene=gene, pathway=pathway)

    def load_herb_pcm(self, filepath):
        df = pd.read_excel(filepath, sheet_name="Sheet2", usecols=["Herb", "Pcs"]).dropna().drop_duplicates().head(8000)
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.write_transaction(self._create_herb_pcm, row['Herb'].strip(), row['Pcs'].strip())

    def load_pcm_gene(self, filepath):
        df = pd.read_csv(filepath, usecols=["ChemicalName", "GeneSymbol"]).dropna().drop_duplicates().head(8000)
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.write_transaction(self._create_pcm_gene, row['ChemicalName'].strip(), row['GeneSymbol'].strip())

    def load_gene_disease(self, filepath):
        df = pd.read_csv(filepath, usecols=["GeneSymbol", "DiseaseName"]).dropna().drop_duplicates().head(8000)
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.write_transaction(self._create_gene_disease, row['GeneSymbol'].strip(), row['DiseaseName'].strip())

    def load_gene_pathway(self, filepath):
        df = pd.read_csv(filepath, usecols=["GeneSymbol", "PathwayName"]).dropna().drop_duplicates().head(8000)
        with self.driver.session() as session:
            for _, row in df.iterrows():
                session.write_transaction(self._create_gene_pathway, row['GeneSymbol'].strip(), row['PathwayName'].strip())

if __name__ == "__main__":
    loader = HerbGraphLoader()
    loader.load_herb_pcm("sample3_updated_filedb.xlsx")
    loader.load_pcm_gene("Associated_genes.csv")
    loader.load_gene_disease("filtered_diseases.csv")     # ✅ Corrected name
    loader.load_gene_pathway("filtered_pathways.csv")     # ✅ Corrected name
    loader.close()
