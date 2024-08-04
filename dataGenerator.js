const fs = require('fs');
const { v4: uuidv4 } = require('uuid');
const { faker } = require('@faker-js/faker');
const connectToMongoDB = require('./mongoConnection.js');

const NUM_TRAINS = 396; // Updated to actual number of trains
const NUM_DAYS = 90;
const DATA_INTERVAL_MINUTES = 1;

function generateLocationData(train_id, startDate, numEntries) {
  const locationData = [];
  let currentDate = new Date(startDate);

  for (let i = 0; i < numEntries; i++) {
    const location = {
      location_id: uuidv4(),
      train_id: train_id,
      timestamp: new Date(currentDate),
      latitude: faker.location.latitude(),
      longitude: faker.location.longitude(),
      speed: faker.number.int({ min: 30, max: 120 }), // Speed in km/h
      direction: faker.number.int({ min: 0, max: 360 }) // Direction in degrees
    };
    locationData.push(location);
    currentDate.setMinutes(currentDate.getMinutes() + DATA_INTERVAL_MINUTES);
  }

  return locationData;
}

async function main() {
    const client = await connectToMongoDB();
    const db = client.db('trainData');
    const collection = db.collection('locations');
  
    for (let trainId = 1; trainId <= NUM_TRAINS; trainId++) {
      const startDate = new Date();
      const numEntries = NUM_DAYS * 24 * 60 / DATA_INTERVAL_MINUTES;
      const locationData = generateLocationData(trainId, startDate, numEntries);
  
      // Insert data into MongoDB
      await collection.insertMany(locationData);
      console.log(`Inserted data for train ${trainId}, inserted IDs: ${result.insertedIds}`);
    }
  
    await client.close();
    console.log('Data generation and insertion complete');
  }
  
  main().catch(console.error);