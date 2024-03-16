const axios = require('axios');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

import getItemDetails from "./details";

async function scrapePage(url) {
    try {
        const response = await axios.get(url);
        const htmlContent = response.data;

        // Parse HTML using jsdom
        const dom = new JSDOM(htmlContent);
        const document = dom.window.document;

        const items = [];

        // Find all elements with class 'cassette js-bukkenCassette'
        const mother = document.querySelectorAll('.cassette.js-bukkenCassette');

        // Loop through each element
        mother.forEach(child => {
            items.push(getItemDetails(child));
        });

        return items;
    } catch (error) {
        console.error('Error:', error.message);
        return [];
    }
}

export default scrapePage;