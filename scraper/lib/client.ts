import { MongoClient } from 'mongodb'

const uri = process.env.MONGO_URI || ''
const client = new MongoClient(uri)

export default client
