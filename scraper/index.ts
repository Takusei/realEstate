import logger from './lib/logger'
import crawler from './cron/crawler'
import client from './lib/client' // <-- Import the client

const main = async () => {
  try {
    logger.info('Start crawl...')
    await crawler()
    logger.info('Crawl finished successfully.')
  } catch (error) {
    logger.error('An error occurred during the crawl process:', error)
    process.exit(1) // Exit with a failure code
  } finally {
    logger.info('Closing database connection.')
    await client.close() // <-- Close the connection
    process.exit(0) // Exit with a success code
  }
}

// Execute the main function
void main()