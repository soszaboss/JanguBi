import json
import os
from bs4 import BeautifulSoup

html_dir = "/app/init/rosary/format/html"
json_path = "/app/init/rosary/format/json/rosary_french.json"

mapping = {
    "joyeux.html": "Joyeux",
    "lumineux.html": "Lumineux",
    "douloureux.html": "Douloureux",
    "glorieux.html": "Glorieux"
}

parsed_data = {}

for filename, group_name in mapping.items():
    filepath = os.path.join(html_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    with open(filepath, 'r') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    mysteries = []
    
    for b_tag in soup.find_all('b'):
        text = b_tag.get_text(separator=" ", strip=True)
        # Look for "Mystère" and ":" which indicates a title row
        if "Mystère" in text and ":" in text:
            # Title part is after the colon
            title_part = text.split(":", 1)[1].strip()
            
            # The next <p> tag within the SAME <td> usually contains the scripture
            parent_td = b_tag.find_parent('td')
            if not parent_td:
                continue
                
            p_tags = parent_td.find_all('p')
            scripture = ""
            
            # The paragraph starting with a guillemet « is the scripture reading
            for p in p_tags:
                p_text = p.get_text(separator=" ", strip=True).replace('\n', ' ').replace('\xa0', ' ')
                if "«" in p_text or '"' in p_text:
                    scripture = p_text
                    break
            
            # Fallback if no quote marks
            if not scripture and len(p_tags) > 0:
                scripture = p_tags[0].get_text(separator=" ", strip=True).replace('\n', ' ').replace('\xa0', ' ')
            
            # We also noticed some cases didn't get picked up without quotation marks
            # Ensure we omit the "Notre Père, 10 Je vous salue Marie" paragraph
            if scripture.startswith("Notre Père"):
               scripture = ""
            
            mysteries.append({
                "title": title_part,
                "scripture": scripture
            })
            
    parsed_data[group_name] = mysteries
    print(f"Extracted {len(mysteries)} mysteries for {group_name}")

# Now update the JSON
try:
    with open(json_path, 'r') as f:
        rosary_json = json.load(f)

    for day, day_data in rosary_json.items():
        if day == "_instructions":
            continue
            
        group_name = day_data.get("group")
        new_mysteries_data = parsed_data.get(group_name)
        if not new_mysteries_data:
            continue
            
        for i, mystery in enumerate(day_data["mysteries"]):
            if i < len(new_mysteries_data):
                mystery["title"] = new_mysteries_data[i]["title"]
                mystery["meditation"] = new_mysteries_data[i]["scripture"]

    # Add introductory explanations to the JSON dict
    rosary_json["_instructions"] = {
        "title": "Comment prier le Rosaire ?",
        "description": "Le Rosaire est une prière méditative de l'Église Catholique. Il consiste en une répétition de prières (Notre Père, Je vous salue Marie, Gloire au Père) tout en méditant sur la vie de Jésus-Christ (les Mystères).",
        "structure_d_une_dizaine": "Une 'dizaine' de chapelet se déroule ainsi : 1. On annonce le Mystère (ex: L'Annonciation), 2. On lit un passage biblique pour méditer, 3. On récite 1 'Notre Père', 4. On récite 10 'Je vous salue Marie' en méditant le mystère, 5. On termine avec 1 'Gloire au Père' et la prière de Fatima."
    }

    with open(json_path, 'w') as f:
        json.dump(rosary_json, f, indent=2, ensure_ascii=False)

    print("Updated rosary_french.json successfully.")
except Exception as e:
    print(f"Error updating JSON: {e}")
