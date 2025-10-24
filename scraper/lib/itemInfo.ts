import {
  z2h, parseBuiltYM, parsePriceToYen,
  parseMonthlyPaymentToYen, parseAreaSqm, parseLayout,
  parseStationBlock, detectFlags
} from "./normalize"

class ItemInfo {
  category: string
  name: string
  address: string
  station: string
  description: string
  image: string
  url: string
  price: string
  price_yen: number | null
  price_monthly_yen: number | null
  size: string
  area_sqm: number | null
  layout_raw: string | null
  rooms: number | null
  ldk: boolean | null
  built_year: number | null
  built_month: number | null
  updateDate: string
  station_line: string | null
  station_name: string | null
  station_walk_minutes: number | null
  flags: {
    pet_ok: boolean,
    south_facing: boolean,
    corner: boolean,
    balcony: boolean,
    tower_mansion: boolean,
  }

  constructor(catalog: string, name: string, address: string, station: string, description: string, image: string, url: string, price: string, size: string, age: string) {
    this.category = z2h(catalog)
    this.name = z2h(name)
    this.address = z2h(address)

    this.station = station
    this.station_line = parseStationBlock(station).line
    this.station_name = parseStationBlock(station).name
    this.station_walk_minutes = parseStationBlock(station).walk_minutes

    this.description = z2h(description)
    this.image = image
    this.url = process.env.BASE_PATH + url

    this.price = price
    this.price_yen = parsePriceToYen(price)
    this.price_monthly_yen = parseMonthlyPaymentToYen(price)

    this.size = size
    this.area_sqm = parseAreaSqm(size)
    this.layout_raw = parseLayout(size).layout_raw
    this.rooms = parseLayout(size).rooms
    this.ldk = parseLayout(size).ldk

    this.built_year = parseBuiltYM(age).built_year
    this.built_month = parseBuiltYM(age).built_month
    this.updateDate = new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Tokyo' })

    this.flags = detectFlags(description, name, catalog)
  }
}


export default ItemInfo
