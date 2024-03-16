import scrapePage from './lib/scrape';
import { getNumbers } from './lib/number';
import { sleep } from 'bun';
const cliProgress = require('cli-progress');
import fs from 'fs';

const progressBar = new cliProgress.SingleBar({}, cliProgress.Presets.shades_classic);

const { totalItems, maxPageNumber} = await getNumbers();

console.log(`Total items: ${totalItems}`);
console.log(`Max page number: ${maxPageNumber}`);

progressBar.start(maxPageNumber, 0);

const items = []
for (let i = 1; i <= maxPageNumber; i++) {
    progressBar.increment();
    const data = await scrapePage(process.env.START_PATH + `&pn=${i}`)
    items.push(...data);
}

fs.writeFileSync(`/home/jaycen/workspace/realEstate/result/data.json`, JSON.stringify(items));

progressBar.stop();