import axios from 'axios'
import { JSDOM } from 'jsdom'

const getItemNumber = (document: any): number => {
  let totalItems = 0

  const totalItemsElement = document.querySelector('.pagination_set-hit') as Element
  const totalItemsText = totalItemsElement?.textContent?.trim() ?? ''
  const totalItemsMatch = totalItemsText.match(/\d+/)
  if (totalItemsMatch !== null) {
    totalItems = parseInt(totalItemsMatch[0])
  }

  return totalItems
}

const getMaxPageNumber = (document: any): number => {
  let maxPageNumber = 0

  const maxPageLinkElement = document.querySelector('.pagination-parts li:last-child a')
  const maxPageLinkHref = maxPageLinkElement.getAttribute('href')
  const maxPageNumberMatch: string[] | null = maxPageLinkHref.match(/pn=(\d+)/)
  if (maxPageNumberMatch !== null) {
    maxPageNumber = parseInt(maxPageNumberMatch[1])
  }
  return maxPageNumber
}

const getNumbers = async (): Promise<{ totalItems: number, maxPageNumber: number }> => {
  const startPath = process.env.START_PATH ?? ''
  const response = await axios.get(startPath)
  const htmlContent: string = response.data // Explicitly type htmlContent as string

  // Parse HTML using jsdom
  const dom = new JSDOM(htmlContent)
  const document = dom.window.document

  const totalItems = getItemNumber(document)
  const maxPageNumber = getMaxPageNumber(document)

  return { totalItems, maxPageNumber }
}

export { getItemNumber, getMaxPageNumber, getNumbers }
