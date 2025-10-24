import scrapePage from '../lib/scrape'
import { getNumbers } from '../lib/number'
import client from '../lib/client'
import logger from '../lib/logger'

const crawler = async (): Promise<void> => {
  logger.info('Start: Crawler is scraping and saving to the database...')
  try {
    const { totalItems, maxPageNumber } = await getNumbers()

    logger.info(`Processing: total items: ${totalItems}, and max page number: ${maxPageNumber}`)

    const allItems = []
    for (let i = 1; i <= maxPageNumber; i++) {
      try {
        // logger.info(`Scraping page ${i} of ${maxPageNumber}...`)
        const data = await scrapePage(process.env.START_PATH + `&pn=${i}`)
        allItems.push(...data)
      } catch (error) {
        logger.error(`Failed to scrape page ${i}: ${error}`)
        // Continue to the next page even if one fails
      }
    }
    logger.info(`${allItems.length} items scraped in total.`)

    const database = client.db(process.env.MONGO_DB_NAME ?? '')
    const collection = database.collection(process.env.MONGO_COLLECTION_NAME ?? '')
    if (allItems.length > 0) {
      logger.info('Inserting scraped items into the database...')
      await collection.insertMany(allItems)
    }
    logger.info('Finished: Crawler has finished scraping and saved to the database.')
  } catch (error) {
    logger.error(`Error: Error scraping and saving to the database: ${error}`)
    // Re-throw the error so the caller (main function) can catch it
    throw error
  }
}

export default crawler