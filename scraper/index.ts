import scrapePage from './lib/scrape';
import { getNumbers } from './lib/number';
import { MongoClient  } from 'mongodb';
import logger from './lib/logger';

const { totalItems, maxPageNumber} = await getNumbers();

logger.info(`Total items: ${totalItems}`);
logger.info(`Max page number: ${maxPageNumber}`);

const items = await Promise.all(
    Array.from({ length: maxPageNumber }, (_, i) => i + 1)
        .map(async (i) => {
            const data = await scrapePage(process.env.START_PATH + `&pn=${i}`);
            return data;
        }) 
);

const uri = process.env.MONGO_URI || '';
const client = new MongoClient(uri);

const run = async () => {
    try {
      const database = client.db(process.env.MONGO_DB_NAME || '');
      const suumo = database.collection(process.env.MONGO_COLLECTION_NAME || '');
      await suumo.insertMany(items.flat());
    } finally {
      await client.close();
    }
}

run().catch(console.dir);