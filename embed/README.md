# 📦 Embedding Generation Script

This directory contains the batch processing script responsible for generating vector embeddings for the real estate data. It reads property listings from MongoDB, uses Google's Vertex AI to create embeddings for each one, and then updates the documents in the database with these vectors.

This is a crucial pre-processing step that enables the main application's vector search capabilities.

---

## 🛠️ Tech Stack

-   **Language**: Python 3.12
-   **Package Management**: [uv](https://github.com/astral-sh/uv)
-   **Embeddings Model**: [Google Vertex AI](https://cloud.google.com/vertex-ai) (`text-multilingual-embedding-002`)
-   **Database**: [MongoDB Atlas](https://www.mongodb.com/atlas)

---

## 🚀 Getting Started

### 1. Set Up Environment Variables

This script requires credentials to connect to MongoDB and Google Cloud. Create a `.env` file in this `embed/` directory.

```env
# .env file

# MongoDB Configuration
MONGO_URI="mongodb+srv://user:password@your-cluster.mongodb.net/?..."
DB_NAME="suumo"
MONGO_COLLECTION_NAME="suumo"

# Google Cloud Configuration
PROJECT_ID="your-gcp-project-id"
```

### 2. Install Dependencies

If you haven't already done so from the parent directory, install the required Python packages using `uv`.

```bash
# Run from the root of the project
uv sync
```

---

## 🏃 Running the Script

To start the embedding process, run the `embed_batch.py` script using `uv`. The `--env-file` flag will load the necessary credentials from your `.env` file.

```bash
uv run --env-file .env embed_batch.py
```

The script will:
1.  Connect to your MongoDB collection.
2.  Find documents that do not yet have an `embedding`.
3.  Generate embeddings for them in batches.
4.  Update the documents with the new `embedding` vector.

This script is designed to be run manually or as a scheduled job whenever new property data is added to the database.