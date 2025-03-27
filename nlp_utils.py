import spacy
import dateparser
from datetime import datetime

nlp = spacy.load("en_core_web_sm")

def extract_entities(user_input):
    doc = nlp(user_input)
    entities = {"departure": None, "destination": None, "date": None}

    for ent in doc.ents:
        if ent.label_ == "GPE":
            if not entities["departure"]:
                entities["departure"] = ent.text
            else:
                entities["destination"] = ent.text
        elif ent.label_ == "DATE":
            parsed_date = dateparser.parse(ent.text)  # Convert to datetime object
            if parsed_date:
                entities["date"] = parsed_date.strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD format
    
     
    return entities


