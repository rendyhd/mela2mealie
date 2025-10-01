import json
import requests
from pathlib import Path
import time
import os
from dotenv import load_dotenv
import re
import uuid
import base64

def format_duration(time_str):
    if not time_str: return ""
    time_str = time_str.lower().strip().replace('m', ' minutes').replace('h', ' hours')
    return time_str.strip()

def parse_nutrition(text):
    if not text: return {}
    nutrition_obj = {}
    cal_match = re.search(r'(\d+)\s*(?:kcal|calories)', text, re.IGNORECASE)
    if cal_match:
        nutrition_obj['calories'] = f"{cal_match.group(1)} kcal"
    return nutrition_obj

def convert_mela_to_mealie_schema(mela_data):
    mealie_recipe = {
        "@context": "https://schema.org", "@type": "Recipe",
        "name": mela_data.get("title", "Untitled Recipe"),
        "id": "", "slug": "", "url": mela_data.get("link", ""),
        "image": "", "author": "",
        "recipeYield": mela_data.get("yield", ""),
        "description": mela_data.get("text", ""),
        "dietaryRestrictions": "", "recipeCuisine": "",
        "ingredients": [], "recipeInstructions": [],
        "cookTime": format_duration(mela_data.get("cookTime")),
        "prepTime": format_duration(mela_data.get("prepTime")),
        "totalTime": format_duration(mela_data.get("totalTime")),
        "nutrition": parse_nutrition(mela_data.get("nutrition")),
    }
    categories = mela_data.get("categories", [])
    if categories:
        mealie_recipe["tags"] = [
            {"id": str(uuid.uuid4()), "name": cat, "slug": re.sub(r'\s+', '-', cat.lower().strip())}
            for cat in categories
        ]
        mealie_recipe["recipeCuisine"] = ",".join(categories)
    if mela_data.get("ingredients"):
        ingredients_text = re.sub(r'^#.*', '', mela_data["ingredients"], flags=re.MULTILINE)
        mealie_recipe["ingredients"] = [line.strip() for line in ingredients_text.split('\n') if line.strip()]
    if mela_data.get("instructions"):
        instructions_text = re.sub(r'#+|\*+', '', mela_data["instructions"])
        mealie_recipe["recipeInstructions"] = [line.strip() for line in instructions_text.split('\n') if line.strip()]
    if mela_data.get("notes"):
        mealie_recipe["notes"] = [{"title": "Note", "text": mela_data.get("notes")}]
    return mealie_recipe


class MealieImporter:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv('MEALIE_HOST', 'http://127.0.0.1:9000')
        self.api_key = os.getenv('MEALIE_API_KEY')
        if not self.api_key:
            raise ValueError("MEALIE_API_KEY not found in .env file")
        self.json_headers = {
            "Authorization": f"Bearer {self.api_key}", "accept": "application/json", "Content-Type": "application/json"
        }
        self.file_headers = {
            "Authorization": f"Bearer {self.api_key}", "accept": "application/json"
        }

    def upload_image_to_recipe(self, recipe_slug, b64_image_data):
        url = f"{self.host}/api/recipes/{recipe_slug}/image"
        print(f"Uploading image to: {url}")
        try:
            image_bytes = base64.b64decode(b64_image_data)
            files = {'image': ('image.heic', image_bytes, 'image/heic')}
            data = {'extension': 'heic'}
            response = requests.put(url, files=files, data=data, headers=self.file_headers)
            response.raise_for_status()
            print(f"Image successfully uploaded for recipe: {recipe_slug}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error uploading image for {recipe_slug}: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
        return None

    def create_recipe_and_get_id(self, recipe_json):
        """Creates a new recipe and returns its ID string."""
        url = f"{self.host}/api/recipes/create/html-or-json"
        import_data = {"data": json.dumps(recipe_json)}
        try:
            response = requests.post(url, json=import_data, headers=self.json_headers)
            response.raise_for_status()
            recipe_id = response.json()
            print(f"Successfully created recipe: {recipe_json['name']} (ID: {recipe_id})")
            return recipe_id
        except requests.exceptions.RequestException as e:
            print(f"Error creating recipe: {recipe_json.get('name', 'N/A')}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return None
            
    def get_recipe_details(self, recipe_id):
        """Fetches the full details for a recipe by its ID."""
        url = f"{self.host}/api/recipes/{recipe_id}"
        print(f"Fetching details for recipe ID: {recipe_id}")
        try:
            response = requests.get(url, headers=self.json_headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for recipe ID {recipe_id}: {e}")
            return None

    def bulk_import_from_directory(self, directory=None):
        if directory is None:
            directory = os.getenv('RECIPES_DIR', './recipes')
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory {directory} does not exist")

        success, failed = 0, 0
        failed_recipes = []
        print(f"\nImporting recipes from {directory}")

        recipe_files = list(directory.glob("*.json")) + list(directory.glob("*.melarecipe"))
        for recipe_file in recipe_files:
            print(f"\nProcessing {recipe_file.name}...")
            try:
                with open(recipe_file, 'r', encoding='utf-8') as f:
                    mela_json = json.load(f)
                
                mealie_schema_json = convert_mela_to_mealie_schema(mela_json)

                # STEP 1: Create the recipe and get its ID
                recipe_id = self.create_recipe_and_get_id(mealie_schema_json)
                
                if not recipe_id:
                    failed += 1
                    failed_recipes.append(recipe_file.name)
                    continue

                # STEP 2: Fetch recipe details to get the slug
                recipe_details = self.get_recipe_details(recipe_id)

                # STEP 3: If an image exists, upload it using the slug
                if recipe_details and mela_json.get("images"):
                    recipe_slug = recipe_details.get('slug')
                    if recipe_slug:
                        self.upload_image_to_recipe(recipe_slug, mela_json["images"][0])
                    else:
                        print(f"Could not find slug for recipe '{recipe_details.get('name')}' to upload image.")
                
                success += 1
                time.sleep(1)

            except Exception as e:
                print(f"FATAL: Error processing {recipe_file.name}: {e}")
                failed += 1
                failed_recipes.append(recipe_file.name)

        print(f"\nImport completed!")
        print(f"Successfully imported: {success} recipes")
        print(f"Failed to import: {failed} recipes")
        if failed_recipes:
            print("\nFailed recipes:")
            for recipe in failed_recipes:
                print(f"- {recipe}")

def main():
    try:
        importer = MealieImporter()
        importer.bulk_import_from_directory()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()