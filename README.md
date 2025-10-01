# Mela to Mealie Migration Script

This script provides a straightforward way to migrate your recipes from the Mela recipe manager app to a self-hosted Mealie instance. It reads `.melarecipe` or `.json` export files from Mela, converts them to the Mealie-compatible schema.org format, and imports them into your Mealie server via its API.

## Features

- **Bulk Import**: Imports all Mela recipe files from a specified directory.
- **Schema Conversion**: Automatically converts Mela's JSON structure to Mealie's required format.
- **Image Uploads**: Uploads the primary image for each recipe.
- **Graceful Handling**: Skips individual recipes that fail to import and provides a summary at the end.
- **Environment-based Configuration**: Uses a `.env` file to keep your sensitive API keys and host information separate from the code.

## Requirements

- Python 3.6+
- A running Mealie instance (v1.0.0 or later recommended)
- A long-lived API token from your Mealie instance

## Setup & Configuration

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install Dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Export Your Mela Recipes:**
    - In the Mela app, select the recipes you want to export.
    - Choose the "Export" option and select the JSON format.
    - Save the exported `.melarecipe` files to a directory.

4.  **Create a `.env` File:**
    Create a file named `.env` in the root of the project directory and add the following configuration variables:

    ```env
    # The full URL of your Mealie instance
    MEALIE_HOST=http://your-mealie-domain.com

    # Your long-lived API token from Mealie
    MEALIE_API_KEY=your-long-lived-api-key

    # The directory where your Mela recipe files are stored
    RECIPES_DIR=./Recipes
    ```
    - You can get a long-lived API token from your Mealie user profile page (`/user/profile`).
    - The `RECIPES_DIR` can be an absolute or relative path.

## Usage

Once the setup is complete, you can run the import script from your terminal:

```bash
python mela-to-mealie.py
```

The script will start processing the files in the directory specified by `RECIPES_DIR`. You will see progress logs in the console, including which recipes were successful and which ones failed.

## How It Works

The script performs the following steps for each recipe file found:
1.  **Read and Parse**: Reads the Mela JSON data from the file.
2.  **Convert**: Transforms the data into a `schema.org/Recipe` JSON object that Mealie understands. This includes mapping fields like title, ingredients, instructions, and timings.
3.  **Create Recipe**: Sends the converted JSON data to the `/api/recipes/create/html-or-json` endpoint to create the base recipe in Mealie.
4.  **Fetch Slug**: After creating the recipe, it fetches the full recipe details to get the unique `slug`.
5.  **Upload Image**: If the recipe has an image, it's uploaded to the `/api/recipes/{slug}/image` endpoint using the obtained slug.

The script waits for 1 second between processing each recipe to avoid overwhelming the Mealie API.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.