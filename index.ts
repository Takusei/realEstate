const axios = require('axios');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
import getItemDetails from "./lib/details";

async function scrapePage(url) {
    try {
        const response = await axios.get(url);
        const htmlContent = response.data;

        // Parse HTML using jsdom
        const dom = new JSDOM(htmlContent);
        const document = dom.window.document;

        const dataSamples = [];

        // Find all elements with class 'cassette js-bukkenCassette'
        const mother = document.querySelectorAll('.cassette.js-bukkenCassette');

        // Loop through each element
        mother.forEach(child => {
            dataSamples.push(getItemDetails(child));
        });

        return dataSamples;
    } catch (error) {
        console.error('Error:', error.message);
        return [];
    }
}

const url = 'https://suumo.jp/jj/common/ichiran/JJ901FC004/?initFlg=1&seniFlg=1&pc=30&ar=030&ra=030013&rnTmp=0215&kb=0&xb=0&newflg=0&km=1&rn=0215&bs=010&bs=011&bs=020';
scrapePage(url)
    .then(data => console.log(data))
    .catch(error => console.error(error));
