const { v4: uuidv4 } = require('uuid');
const { faker } = require('@faker-js/faker');
const cors = require('cors');
const connectToMongoDB = require('./mongoConnection.js');

const NUM_TRAINS = 396;
const NUM_DAYS = 90;
const DATA_INTERVAL_MINUTES = 1;
const BATCH_SIZE = 1000;

// Sri Lanka bounding box
const SRI_LANKA_BOUNDS = {
  minLat: 5.912,
  maxLat: 9.842,
  minLng: 79.695,
  maxLng: 81.787
};

function getRandomSriLankanCoordinates() {
  return {
    latitude: faker.number.float({ min: SRI_LANKA_BOUNDS.minLat, max: SRI_LANKA_BOUNDS.maxLat }),
    longitude: faker.number.float({ min: SRI_LANKA_BOUNDS.minLng, max: SRI_LANKA_BOUNDS.maxLng })
  };
}

function generatePathSegments(startCoords, endCoords, numSegments) {
  const segments = [];
  const latIncrement = (endCoords.latitude - startCoords.latitude) / numSegments;
  const lngIncrement = (endCoords.longitude - startCoords.longitude) / numSegments;
  
  for (let i = 0; i < numSegments; i++) {
    const segmentStart = {
      latitude: startCoords.latitude + latIncrement * i,
      longitude: startCoords.longitude + lngIncrement * i
    };
    const segmentEnd = {
      latitude: startCoords.latitude + latIncrement * (i + 1),
      longitude: startCoords.longitude + lngIncrement * (i + 1)
    };
    segments.push({ start: segmentStart, end: segmentEnd });
  }

  return segments;
}

function generateLocationData(train_id, startDate, numEntries, segments) {
  const locationData = [];
  let currentDate = new Date(startDate);

  for (let i = 0; i < numEntries; i++) {
    const segmentIndex = Math.floor(i / (numEntries / segments.length));
    const segment = segments[segmentIndex];
    const segmentProgress = (i % (numEntries / segments.length)) / (numEntries / segments.length);

    const location = {
      location_id: uuidv4(),
      train_id: train_id,
      timestamp: new Date(currentDate),
      latitude: segment.start.latitude + (segment.end.latitude - segment.start.latitude) * segmentProgress,
      longitude: segment.start.longitude + (segment.end.longitude - segment.start.longitude) * segmentProgress,
      speed: faker.number.int({ min: 30, max: 120 }), // Speed in km/h
      direction: faker.number.int({ min: 0, max: 360 }) // Direction in degrees
    };

    locationData.push(location);
    currentDate.setMinutes(currentDate.getMinutes() + DATA_INTERVAL_MINUTES);
  }

  return locationData;
}

async function insertDataInBatches(collection, data) {
  for (let i = 0; i < data.length; i += BATCH_SIZE) {
    const batch = data.slice(i, i + BATCH_SIZE);
    try {
      await collection.insertMany(batch);
      console.log(`Inserted batch ${i / BATCH_SIZE + 1}`);
    } catch (err) {
      console.error(`Error inserting batch ${i / BATCH_SIZE + 1}:`, err);
    }
  }
}

async function main() {
  const client = await connectToMongoDB();
  const db = client.db('trainData');
  const collection = db.collection('locations');

  try {
    for (let trainId = 1; trainId <= NUM_TRAINS; trainId++) {
      const startDate = new Date();
      const numEntries = (NUM_DAYS * 24 * 60) / DATA_INTERVAL_MINUTES;
      const startCoords = getRandomSriLankanCoordinates();
      const endCoords = getRandomSriLankanCoordinates();
      const numSegments = faker.number.int({ min: 5, max: 15 }); // Number of segments in the path
      const pathSegments = generatePathSegments(startCoords, endCoords, numSegments);
      const locationData = generateLocationData(trainId, startDate, numEntries, pathSegments);

      // Insert data into MongoDB in batches
      await insertDataInBatches(collection, locationData);
      console.log(`Inserted data for train ${trainId}`);
    }
  } catch (err) {
    console.error('Error during data generation and insertion:', err);
  } finally {
    await client.close();
    console.log('Data generation and insertion complete');
  }
}

main().catch(console.error);