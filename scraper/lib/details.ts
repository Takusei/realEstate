import ItemInfo from './itemInfo'

const getInfoFromTable = (item: any): string[] => {
  const tableInfo: string[] = []
  const firstTableRows = item.querySelectorAll('.infodatabox-boxgroup .listtable:nth-of-type(1) tbody tr')
  firstTableRows.forEach((row: any) => {
    const cells = row.querySelectorAll('td')
    cells.forEach((cell: HTMLElement) => { // Specify the type of 'cell' as 'HTMLElement'
      tableInfo.push((cell?.textContent ?? '').trim().replace(/\s+/g, ' ')) // Remove extra whitespace
    })
  })

  const secondTableRows = item.querySelectorAll('.infodatabox-boxgroup .listtable:nth-of-type(2) tbody tr')
  secondTableRows.forEach((row: any) => {
    const cells = row.querySelectorAll('td')
    cells.forEach((cell: HTMLElement) => { // Specify the type of 'cell' as 'HTMLElement'
      tableInfo.push((cell?.textContent ?? '').trim().replace(/\s+/g, ' ')) // Remove extra whitespace
    })
  })
  return tableInfo
}

const getItemDetails = (item: any): ItemInfo => {
  const category: string = item.querySelector('.cassettebox-header .cassettebox-hpct').textContent.trim()
  const name: string = item.querySelector('.cassettebox-header .cassettebox-title a').textContent.trim()
  const description: string = item.querySelector('.infodatabox-lead').textContent.trim()
  const url: string = item.querySelector('.cassettebox-header .cassettebox-title a').href
  const image: string = item.querySelector('.cassettebox-body .ui-media .infodatabox-object img').getAttribute('rel')

  const tableInfo = getInfoFromTable(item)
  const address: string = tableInfo[0]
  const station: string = tableInfo[1] + ' ' + tableInfo[2]
  const price: string = tableInfo[3]
  const size: string = tableInfo[4]
  const age: string = tableInfo[5]

  return new ItemInfo(category, name, address, station, description, image, url, price, size, age)
}

export default getItemDetails
