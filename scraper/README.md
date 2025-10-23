# Suumo.jp Real Estate Scraper

This is the scraper component of the Real Estate project. It is a Bun application responsible for collecting property data from [Suumo.jp](https://suumo.jp/).

## Prerequisites

Before you begin, ensure you have the following installed:
- [Bun](https://bun.sh/) (v1.0.31 or later)
- A running MongoDB instance accessible to the scraper.

## Installation

1.  Navigate to the `scraper` directory.
2.  Install the required dependencies:
    ```bash
    bun install
    ```

## Configuration

The application requires a `.env` file for environment-specific configurations.

1.  Create a `.env` file in the root of the `scraper` directory.
    ```bash
    touch .env
    ```

2.  Add the necessary environment variables to the `.env` file. See the example below.

    ```env
    # .env example
    # DB
    MONGO_URI='mongodb://admin:password@localhost:27017/?authSource=admin'
    MONGO_DB_NAME='suumo'
    MONGO_COLLECTION_NAME='suumo'

    # Suumo
    START_PATH='https://suumo.jp/jj/common/ichiran/JJ901FC004/?initFlg=1&seniFlg=1&pc=30&ar=030&ra=030013&rnTmp=0215&kb=0&xb=0&newflg=0&km=1&rn=0215&bs=010&bs=011&bs=020'
    BASE_PATH='https://suumo.jp'

    # Cron
    CRON_SCHEDULE='00 23 * * *'
    ```

### Environment Variables

-   `MONGO_URI`: **(Required)** The connection string for your MongoDB database. The hostname will vary depending on your environment:
    -   **Local Machine:** `localhost`
    -   **Docker Compose:** `mongodb` (the service name)
    -   **Kubernetes:** `mongodb.realestate.svc.cluster.local`
-   `MONGO_DB_NAME`: **(Required)** The name of the database to use in MongoDB.
-   `MONGO_COLLECTION_NAME`: **(Required)** The name of the collection where scraped data will be stored.
-   `START_PATH`: **(Required)** The initial URL for the Suumo.jp search results to begin scraping.
-   `BASE_PATH`: **(Required)** The base URL for Suumo.jp, used for constructing absolute URLs from relative paths.
-   `CRON_SCHEDULE`: **(Required)** The cron schedule for running the scraper job automatically (e.g., `'00 23 * * *'` for every day at 23:00).

## Running the Scraper

To execute the scraper script, run the following command from within the `scraper` directory:

```bash
bun run index.ts
```

---

This project was created using `bun init` in bun v1.0.31. Bun is a fast, all-in-one JavaScript runtime.
