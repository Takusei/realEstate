import logger from './lib/logger'
import crawler from './cron/crawler'
// import cron from 'node-cron'

const schedule = process.env.CRON_SCHEDULE ?? '* */1 * * * *'

logger.info('Start first crawl...')

await crawler()

// This is not needed when using Cloud Scheduler
// logger.info(`Cron job is scheduled to run at ${schedule}`)

// // eslint-disable-next-line @typescript-eslint/no-misused-promises
// cron.schedule(schedule, async () => {
//   await crawler()
// })
