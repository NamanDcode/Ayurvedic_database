from flask import Flask, render_template, request, jsonify
from neo4j import GraphDatabase
import pandas as pd

app = Flask(__name__)

# ---------- Load Dropdown Data Only ----------
herb_pcm_df = pd.read_excel("sample3_updated_filedb.xlsx", sheet_name="Sheet2", usecols=["Herb", "Pcs"]).dropna().head(8000)
herbs = sorted(herb_pcm_df["Herb"].unique())

# ---------- Neo4j Setup ----------
uri = "bolt://localhost:7687"
username = "neo4j"
password = "july1234"
driver = GraphDatabase.driver(uri, auth=(username, password))

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html", herbs=herbs)

@app.route("/get_graph", methods=["POST"])
def get_graph():
    data = request.get_json()
    selected = data.get("selected")
    graph_type = data.get("type")

    if graph_type != "herb" or not selected:
        return jsonify({"nodes": [], "edges": [], "message": "Please select a Herb to view the graph."})

    cypher_query = """
    MATCH (h:Herb {name: $selected})
    OPTIONAL MATCH (h)-[:HAS_PCM]->(p:PCM)
    OPTIONAL MATCH (p)-[:INTERACTS_WITH]->(g:Gene)
    OPTIONAL MATCH (g)-[:GENE_ASSOCIATED_WITH]->(d:Disease)
    OPTIONAL MATCH (g)-[:GENE_INVOLVED_IN]->(pw:Pathway)
    RETURN h, p, g, d, pw
    LIMIT 100
    """

    with driver.session() as session:
        try:
            result = session.run(cypher_query, selected=selected)

            nodes = {}
            edges = []

            def add_node(node, label, color, shape="dot"):
                if node and node.id not in nodes:
                    nodes[node.id] = {
                        "id": node.id,
                        "label": node.get("name"),
                        "group": label,
                        "color": color,
                        "shape": shape
                    }

            for record in result:
                h = record.get("h")
                p = record.get("p")
                g = record.get("g")
                d = record.get("d")
                pw = record.get("pw")

                add_node(h, "Herb", "green")
                add_node(p, "PCM", "orange")
                add_node(g, "Gene", "skyblue")
                add_node(d, "Disease", "red", "diamond")
                add_node(pw, "Pathway", "purple", "ellipse")

                if h and p:
                    edges.append({"from": h.id, "to": p.id, "label": "HAS_PCM"})
                if p and g:
                    edges.append({"from": p.id, "to": g.id, "label": "INTERACTS_WITH"})
                if g and d:
                    edges.append({"from": g.id, "to": d.id, "label": "GENE_ASSOCIATED_WITH"})
                if g and pw:
                    edges.append({"from": g.id, "to": pw.id, "label": "GENE_INVOLVED_IN"})

            return jsonify({
                "nodes": list(nodes.values()),
                "edges": edges
            })

        except Exception as e:
            print("Error:", e)
            return jsonify({"error": str(e), "message": "Something went wrong while fetching data."}), 500

if __name__ == "__main__":
    app.run(debug=True)
