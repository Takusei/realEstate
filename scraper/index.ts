import logger from './lib/logger'
import crawler from './cron/crawler'
import cron from 'node-cron'

const schedule = process.env.CRON_SCHEDULE || '* */1 * * * *'

logger.info(`Cron job is scheduled to run at ${schedule}`)

cron.schedule(schedule, async () => {
  logger.info('Scraping Suumo to get the latest items...')

  await crawler()

  logger.info('Suumo items have been scraped and saved to the database.')
})
