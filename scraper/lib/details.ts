import ItemInfo from "./itemInfo";

const getInfoFromTable = (item) => {
    const tableInfo: string[] = []
    const firstTableRows = item.querySelectorAll('.infodatabox-boxgroup .listtable:nth-of-type(1) tbody tr');
    firstTableRows.forEach((row) => {
        const cells = row.querySelectorAll('td'); 
        cells.forEach((cell) => { 
            tableInfo.push(cell.textContent.trim().replace(/\s+/g, ' ')); // Remove extra whitespace
        });
    });

    const secondTableRows = item.querySelectorAll('.infodatabox-boxgroup .listtable:nth-of-type(2) tbody tr');
    secondTableRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
            tableInfo.push(cell.textContent.trim().replace(/\s+/g, ' ')); // Remove extra whitespace
        });
    });
    return tableInfo
}

const getItemDetails = (item: any) => {

    const catagory = item.querySelector('.cassettebox-header .cassettebox-hpct').textContent.trim();
    const name = item.querySelector('.cassettebox-header .cassettebox-title a').textContent.trim();
    const description = item.querySelector('.infodatabox-lead').textContent.trim();
    const url = item.querySelector('.cassettebox-header .cassettebox-title a').href;
    const image = item.querySelector('.cassettebox-body .ui-media .infodatabox-object img').getAttribute('rel');
    
    const tableInfo= getInfoFromTable(item);
    const address = tableInfo[0];
    const station = tableInfo[1] + ' ' + tableInfo[2];
    const price = tableInfo[3];
    const size = tableInfo[4];
    const age = tableInfo[5];

    return new ItemInfo(catagory, name, address, station, description, image, url, price, size, age);
}

export default getItemDetails; 