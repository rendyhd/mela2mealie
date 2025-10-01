"""
A script to upload Mela recipes (.melarecipe) to a Mealie instance.

This script reads all `.melarecipe` files from a specified directory,
parses them, and uploads them to a Mealie instance using the Mealie API.

SETUP:
1.  **Install dependencies:**
    pip install requests

2.  **Update Configuration:**
    -   `MEALIE_URL`: Set this to the URL of your Mealie instance (e.g., "http://192.168.1.100:9000").
    -   `API_TOKEN`: Set this to a long-lived API token generated from your Mealie user profile.
    -   `RECIPES_DIR`: Set this to the directory containing your `.melarecipe` export files.

3.  **Place Recipe Files:**
    -   Create the directory specified in `RECIPES_DIR` (default is "exports").
    -   Place your `.melarecipe` files inside this directory.

4.  **Run the script:**
    python upload_recipes.py
"""
import os
import json
import requests
import base64
from io import BytesIO

# --- Configuration ---
# TODO: Update these values with your Mealie instance details
MEALIE_URL = "http://your-mealie-instance.com"
API_TOKEN = "your-long-lived-api-token"
RECIPES_DIR = "exports"  # Directory containing .melarecipe files

def get_access_token(url, token):
    """
    Authenticates with the Mealie API using a long-lived token to get a
    short-lived JWT access token.
    """
    try:
        # Note: The endpoint for API tokens is /api/auth/token/api
        response = requests.post(f"{url}/api/auth/token/api", json={"token": token})
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        if e.response:
            print(f"Response from server: {e.response.text}")
        return None

def upload_recipe(mealie_url, headers, mela_recipe):
    """
    Uploads a single Mela recipe to Mealie.
    """
    recipe_name = mela_recipe.get("title", "Untitled Recipe")
    print(f"Processing '{recipe_name}'...")

    # Step 1: Create a new recipe to get a slug
    try:
        create_payload = {"name": recipe_name}
        response = requests.post(f"{mealie_url}/api/recipes", headers=headers, json=create_payload)
        response.raise_for_status()
        recipe_slug = response.json()  # The response body is the slug string
    except requests.exceptions.RequestException as e:
        print(f"  - FAILED: Could not create recipe. Error: {e}")
        if e.response:
            print(f"  - Response: {e.response.text}")
        return

    # Step 2: Map Mela recipe data to Mealie's PATCH format
    # Combine description and notes
    description = mela_recipe.get("text", "")
    if mela_recipe.get("notes"):
        description += f"\n\n--- Notes ---\n{mela_recipe.get('notes')}"

    # Parse ingredients into Mealie format
    ingredients = []
    if mela_recipe.get("ingredients"):
        for line in mela_recipe["ingredients"].split('\n'):
            if line.strip():
                ingredients.append({"note": line.strip()})

    # Parse instructions into Mealie format
    instructions = []
    if mela_recipe.get("instructions"):
        for i, line in enumerate(mela_recipe["instructions"].split('\n')):
            if line.strip():
                instructions.append({"text": line.strip()})

    patch_payload = {
        "description": description,
        "recipeCategory": [{"name": cat} for cat in mela_recipe.get("categories", [])],
        "tags": [],  # Mela doesn't have a separate tags field
        "recipeYield": mela_recipe.get("yield", ""),
        "prepTime": mela_recipe.get("prepTime", ""),
        "cookTime": mela_recipe.get("cookTime", ""),
        "totalTime": mela_recipe.get("totalTime", ""),
        "recipeIngredient": ingredients,
        "recipeInstructions": instructions,
        "orgURL": mela_recipe.get("link", ""),
    }

    # Step 3: Update the recipe with the full details
    try:
        response = requests.patch(f"{mealie_url}/api/recipes/{recipe_slug}", headers=headers, json=patch_payload)
        response.raise_for_status()
        print(f"  - SUCCESS: Recipe '{recipe_name}' created.")
    except requests.exceptions.RequestException as e:
        print(f"  - FAILED: Could not update recipe. Error: {e}")
        if e.response:
            print(f"  - Response: {e.response.text}")
        return # Stop if we can't update the main details

    # Step 4: Upload the first image, if it exists
    if mela_recipe.get("images"):
        try:
            base64_image = mela_recipe["images"][0]
            image_data = base64.b64decode(base64_image)
            image_file = BytesIO(image_data)

            files = {'image': ('recipe_image.jpg', image_file, 'image/jpeg')}

            response = requests.post(f"{mealie_url}/api/recipes/{recipe_slug}/image", headers=headers, files=files)
            response.raise_for_status()
            print(f"  - SUCCESS: Image uploaded for '{recipe_name}'.")
        except Exception as e:
            print(f"  - WARNING: Failed to upload image. Error: {e}")


def main():
    """
    Main function to run the recipe migration script.
    """
    if MEALIE_URL == "http://your-mealie-instance.com" or API_TOKEN == "your-long-lived-api-token":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! PLEASE UPDATE MEALIE_URL AND API_TOKEN IN THE SCRIPT !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return

    # Create the exports directory if it doesn't exist
    if not os.path.isdir(RECIPES_DIR):
        print(f"Directory '{RECIPES_DIR}' not found.")
        print(f"Please create it and place your .melarecipe files inside.")
        return

    access_token = get_access_token(MEALIE_URL, API_TOKEN)
    if not access_token:
        print("Could not authenticate with Mealie. Please check your URL and API token.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    print("-" * 30)
    print(f"Starting recipe upload from '{RECIPES_DIR}' to '{MEALIE_URL}'")
    print("-" * 30)

    recipe_files = [f for f in os.listdir(RECIPES_DIR) if f.endswith(".melarecipe")]

    if not recipe_files:
        print(f"No .melarecipe files found in '{RECIPES_DIR}'.")
        return

    for filename in recipe_files:
        filepath = os.path.join(RECIPES_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                mela_recipe = json.load(f)
                upload_recipe(MEALIE_URL, headers, mela_recipe)
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from {filename}. Skipping.")
            except Exception as e:
                print(f"An unexpected error occurred processing {filename}: {e}. Skipping.")

    print("-" * 30)
    print("Upload process finished.")
    print("-" * 30)

if __name__ == "__main__":
    main()