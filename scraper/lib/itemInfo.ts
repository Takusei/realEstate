class ItemInfo {
    category: string;
    name: string;
    address: string;
    station: string;
    description: string;
    image: string;
    url: string;
    price: string;
    size: string;
    age: string;

    constructor(catalog: string, name: string, address: string, station: string, description: string, image: string, url: string, price: string, size: string, age: string) {
        this.category = catalog;
        this.name = name;
        this.address = address;
        this.station = station;
        this.description = description;
        this.image = image;
        this.url = url;
        this.price = price;
        this.size = size;
        this.age = age;
    }
}

export default ItemInfo;