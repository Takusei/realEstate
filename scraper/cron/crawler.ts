import scrapePage from '../lib/scrape';
import { getNumbers } from '../lib/number';
import client from '../lib/client';
import logger from '../lib/logger';

const crawler = async () => {
      logger.info('Crawler is scraping and saving to the database...');
      try {
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

            const database = client.db(process.env.MONGO_DB_NAME || '');
            const collection = database.collection(process.env.MONGO_COLLECTION_NAME || '');
            await collection.insertMany(items.flat());
      } finally {
            await client.close();
      }
      logger.info('Crawler has finished scraping and saving to the database.');
}

export default crawler;