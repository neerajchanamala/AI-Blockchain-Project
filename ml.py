import pytesseract
from PIL import Image
import pandas as pd
import re
import os
from tkinter import Tk, filedialog

def normalize(text):
    return re.sub(r'[^a-z0-9 ]', '', text.lower().strip())

def analyze_ingredients_from_image(image_path, dataset_path="ingredient_dataset.csv"):
    img = Image.open(image_path)
    extracted_text = pytesseract.image_to_string(img)

    harmful_df = pd.read_csv(dataset_path)
    harmful_df.dropna(subset=["Ingredient"], inplace=True)
    harmful_df["Reason"] = harmful_df["Reason"].fillna("No reason provided")

    extracted_ingredients = re.split(r',|\n', extracted_text)
    extracted_ingredients = [normalize(i) for i in extracted_ingredients if len(i.strip()) > 2 and i.count(' ') <= 3]

    harmful_df['Normalized'] = harmful_df['Ingredient'].apply(normalize)
    normalized_dataset = harmful_df['Normalized'].tolist()

    harmful_found = []
    seen_ingredients = set()  # to track duplicates
    for item in extracted_ingredients:
        for idx, harmful_item in enumerate(normalized_dataset):
            if harmful_item in item or item in harmful_item:
                original_ing = harmful_df.loc[idx, 'Ingredient']
                if original_ing not in seen_ingredients:
                    reason = harmful_df.loc[idx, 'Reason']
                    harmful_found.append({"name": original_ing, "reason": reason, "status": "Harmful"})
                    seen_ingredients.add(original_ing)
                break


    return harmful_found

# Redirect run_model to actual function used by Flask
def run_model(image_path):
    return analyze_ingredients_from_image(image_path)

# For local testing (optional)
if __name__ == "__main__":
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select an image file")
    if file_path and os.path.exists("ingredient_dataset.csv"):
        results = analyze_ingredients_from_image(file_path)
        print("Analysis Results:", results)
    else:
        print("❌ Image or CSV file not found. Make sure both are available.")
