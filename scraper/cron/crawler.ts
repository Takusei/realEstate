import scrapePage from '../lib/scrape'
import { getNumbers } from '../lib/number'
import client from '../lib/client'
import logger from '../lib/logger'

const crawler = async (): Promise<void> => {
  logger.info('Start: Crawler is scraping and saving to the database...')
  try {
    const { totalItems, maxPageNumber } = await getNumbers()

    logger.info(`Processing: total items: ${totalItems}, and max page number: ${maxPageNumber}`)

    const items = await Promise.all(
      Array.from({ length: maxPageNumber }, (_, i) => i + 1)
        .map(async (i) => {
          const data = await scrapePage(process.env.START_PATH + `&pn=${i}`)
          return data
        })
    )

    const database = client.db(process.env.MONGO_DB_NAME ?? '')
    const collection = database.collection(process.env.MONGO_COLLECTION_NAME ?? '')
    // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
    await collection.insertMany(items.flat())
  } catch (error) {
    logger.error(`Error: Error scraping and saving to the database: ${error}`)
  }
  logger.info('Finished: Crawler has finished scraping and saved to the database.')
}

export default crawler
