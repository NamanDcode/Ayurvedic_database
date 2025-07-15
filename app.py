from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)


df = pd.read_excel("data.xlsx")

synonym_df = pd.read_excel("sanskrit_names.xlsx", header=1)
synonym_df['Modern Name'] = synonym_df['Modern Name'].astype(str).str.strip().str.lower()
synonym_df['Sanskrit Name'] = synonym_df['Sanskrit Name'].astype(str).str.strip()

# Clean AF-Ingredient Table
af_ingredient_df = df[['Table 2. AF-Ingredients data', 'Unnamed: 5']].dropna()
af_ingredient_df.columns = ['Formulation', 'Ingredient']
af_ingredient_df = af_ingredient_df[af_ingredient_df['Formulation'] != 'AF']
af_ingredient_df['Ingredient'] = af_ingredient_df['Ingredient'].astype(str).str.strip().str.lower()

# Clean AF-Indication Table
af_indication_df = df[['Table 3. AF-Indications data', 'Unnamed: 8']].dropna()
af_indication_df.columns = ['Formulation', 'Indication']
af_indication_df = af_indication_df[af_indication_df['Formulation'] != 'AF']

# Clean Indication MeSH Table
indication_mesh_df = df[['Table 5. Disease mapping', 'Unnamed: 14', 'Unnamed: 15']].dropna()
indication_mesh_df.columns = ['Indication', 'MeSH Descriptor', 'MeSH Code']
indication_mesh_df = indication_mesh_df[indication_mesh_df['Indication'] != 'Indication']

# Create mapping 
formulation_to_ingredients = af_ingredient_df.groupby('Formulation')['Ingredient'].apply(set).to_dict()
formulation_to_indications = af_indication_df.groupby('Formulation')['Indication'].apply(set).to_dict()
ingredient_to_formulations = af_ingredient_df.groupby('Ingredient')['Formulation'].apply(set).to_dict()
indication_to_formulations = af_indication_df.groupby('Indication')['Formulation'].apply(set).to_dict()

#
all_formulations = sorted(set(af_ingredient_df['Formulation']))
all_ingredients = sorted(set(af_ingredient_df['Ingredient']))
all_indications = sorted(set(af_indication_df['Indication']))

def get_sanskrit_name(modern_name):
    modern_name_clean = modern_name.strip().lower()
    match = synonym_df[synonym_df['Modern Name'] == modern_name_clean]
    if not match.empty:
        return match['Sanskrit Name'].values[0]
    else:
        fuzzy_matches = synonym_df[synonym_df['Modern Name'].str.contains(modern_name_clean, na=False)]
        if not fuzzy_matches.empty:
            return fuzzy_matches['Sanskrit Name'].values[0]
        else:
            print(f"[Unmatched Ingredient] '{modern_name}' not found in Sanskrit synonym file.")
            return "N/A"

@app.route("/", methods=["GET", "POST"])
def index():
    search_type = None
    selected_values = []
    results = {}

    if request.method == "POST":
        search_type = request.form.get("search_type")
        selected_values = request.form.getlist("selected_values")

        if search_type == "Formulation" and selected_values:
            formulation = selected_values[0]
            results["Formulation"] = formulation

            ingredients = list(formulation_to_ingredients.get(formulation, []))
            enriched_ingredients = [{"Modern": ing, "Sanskrit": get_sanskrit_name(ing)} for ing in ingredients]
            results["Ingredients"] = enriched_ingredients
            results["Indications"] = list(formulation_to_indications.get(formulation, []))

        elif search_type == "Ingredient" and selected_values:
            selected_set = set([s.strip().lower() for s in selected_values])
            formulations_lists = [ingredient_to_formulations.get(ing, set()) for ing in selected_set]
            common_formulations = set.intersection(*formulations_lists) if formulations_lists else set()

            if common_formulations:
                results["Formulations"] = []
                for form in common_formulations:
                    ingredients = list(formulation_to_ingredients.get(form, []))
                    enriched_ingredients = [{
                        "Modern": ing,
                        "Sanskrit": get_sanskrit_name(ing),
                        "URL": f"/ingredient/{ing}"
                    } for ing in ingredients]
                    results["Formulations"].append({
                        "Formulation": form,
                        "Ingredients": enriched_ingredients
                    })
                results["SelectedIngredients"] = list(selected_set)
            else:
                results["Message"] = "There is no formulation that contains all these ingredients."

        elif search_type == "Indication" and selected_values:
            if len(selected_values) > 5:
                results["Error"] = "You can select a maximum of 5 indications."
            else:
                selected_set = set(selected_values)
                formulations_lists = [indication_to_formulations.get(ind, set()) for ind in selected_set]
                common_formulations = set.intersection(*formulations_lists) if formulations_lists else set()

                if common_formulations:
                    results["Formulations"] = list(common_formulations)
                    results["SelectedIndications"] = []
                    for ind in selected_set:
                        row = indication_mesh_df[indication_mesh_df['Indication'] == ind]
                        if not row.empty:
                            desc = row['MeSH Descriptor'].values[0]
                            code = row['MeSH Code'].values[0]
                            results["SelectedIndications"].append({
                                "Indication": ind,
                                "Descriptor": desc,
                                "Code": code
                            })
                else:
                    results["Message"] = "There is no formulation that treats all the selected indications."

    return render_template(
        "index.html",
        search_type=search_type,
        all_formulations=all_formulations,
        all_ingredients=all_ingredients,
        all_indications=all_indications,
        selected_values=selected_values,
        results=results
    )

@app.route("/ingredient/<name>")
def ingredient_detail(name):
    modern_name = name.strip().lower()
    syn_row = synonym_df[synonym_df['Modern Name'] == modern_name]
    sanskrit = syn_row['Sanskrit Name'].values[0] if not syn_row.empty else "N/A"

    formulations = ingredient_to_formulations.get(modern_name, set())
    formulation_data = []
    for form in formulations:
        other_ings = formulation_to_ingredients.get(form, set()) - {modern_name}
        enriched = [{"Modern": ing, "Sanskrit": get_sanskrit_name(ing), "URL": f"/ingredient/{ing}"} for ing in other_ings]
        formulation_data.append({
            "Formulation": form,
            "OtherIngredients": enriched
        })

    return render_template("ingredient_detail.html",
                           modern=modern_name,
                           sanskrit=sanskrit,
                           formulation_data=formulation_data)

if __name__ == "__main__":
    app.run(debug=True)
