const axios = require('axios');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

const getItemNumber = (document) => {
    let totalItems = 0;

    const totalItemsElement = document.querySelector('.pagination_set-hit');
    if (totalItemsElement) {
        const totalItemsText = totalItemsElement.textContent.trim();
        const totalItemsMatch = totalItemsText.match(/\d+/);
        if (totalItemsMatch) {
            totalItems = parseInt(totalItemsMatch[0]);
        }
    }
    return totalItems
}

const getMaxPageNumber = (document) => {
    let maxPageNumber = 0;

    const maxPageLinkElement = document.querySelector('.pagination-parts li:last-child a');
    if (maxPageLinkElement) {
        const maxPageLinkHref = maxPageLinkElement.getAttribute('href');
        const maxPageNumberMatch = maxPageLinkHref.match(/pn=(\d+)/);
        if (maxPageNumberMatch) {
            maxPageNumber = parseInt(maxPageNumberMatch[1]);
        }
    }
    return maxPageNumber
}

const getNumbers = async () => {
    const response = await axios.get(process.env.START_PATH);
    const htmlContent = response.data;

    // Parse HTML using jsdom
    const dom = new JSDOM(htmlContent);
    const document = dom.window.document;

    const totalItems = getItemNumber(document);
    const maxPageNumber = getMaxPageNumber(document);
    
    return { totalItems, maxPageNumber }
}

export { getItemNumber, getMaxPageNumber, getNumbers }