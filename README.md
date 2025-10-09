# Mela to Mealie Importer

This script imports recipes from Mela's JSON export format into a Mealie instance. It handles converting the recipe data to Mealie's format, creating the recipe via the Mealie API, and uploading associated images.

## Features

- Converts Mela recipe JSON to Mealie's schema.
- Handles ingredients, instructions, categories (as tags), and notes.
- Parses cook, prep, and total times.
- Extracts calorie information from nutrition data.
- Uploads the first image associated with a Mela recipe.
- Provides a bulk import feature to process a directory of Mela recipe files.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Create a `.env` file:**
    Copy the `.env.template` file to `.env`:
    ```bash
    cp .env.template .env
    ```
    Then, edit the `.env` file with your Mealie instance details:
    ```
    MEALIE_HOST=http://your-mealie-instance.com
    MEALIE_API_KEY=your-long-lived-api-token
    RECIPES_DIR=./Recipes
    ```
    - `MEALIE_HOST`: The full URL to your Mealie instance.
    - `MEALIE_API_KEY`: A long-lived API token generated from your Mealie user profile.
    - `RECIPES_DIR`: The directory where your Mela recipe export files (`.melarecipe` or `.json`) are stored.

4.  **Export recipes from Mela:**
    - In Mela, select the recipes you want to export.
    - Choose the "Export" option and select the JSON format.
    - Save the exported files into the directory specified by `RECIPES_DIR`.

## Usage

Once the setup is complete, you can run the importer script:

```bash
python mela-to-mealie.py
```

The script will scan the `RECIPES_DIR` for `.melarecipe` and `.json` files, process each one, and upload it to your Mealie instance. The progress will be printed to the console.

## How It Works

The script performs the following steps for each recipe file:

1.  **Reads the Mela JSON file.**
2.  **Converts the data** to the Mealie API's expected JSON format.
3.  **Creates the recipe** in Mealie by calling the `/api/recipes/create/html-or-json` endpoint.
4.  **Fetches the newly created recipe's details** to get its `slug`.
5.  **Uploads the recipe image** (if one exists) to the `/api/recipes/{slug}/image` endpoint.

A 1-second delay is included between processing each recipe to avoid overwhelming the Mealie API.