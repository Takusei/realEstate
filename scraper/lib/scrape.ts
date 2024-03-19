import axios from 'axios'
import { JSDOM } from 'jsdom'
import logger from './logger'

import getItemDetails from './details'

async function scrapePage (url: string): Promise<any[]> {
  try {
    const response = await axios.get(url)
    const htmlContent: string = response.data

    // Parse HTML using jsdom
    const dom = new JSDOM(htmlContent)
    const document = dom.window.document

    const items: any = []

    // Find all elements with class 'cassette js-bukkenCassette'
    const mother = document.querySelectorAll('.cassette.js-bukkenCassette')

    // Loop through each element
    mother.forEach((child: any) => {
      items.push(getItemDetails(child))
    })

    return items
  } catch (error) {
    logger.error(`Error scraping ${String(url)}: ${String(error)}`)
    return []
  }
}

export default scrapePage
