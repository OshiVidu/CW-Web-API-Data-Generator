const { MongoClient } = require('mongodb');

const uri = 'mongodb+srv://vidurangioshi:fPMtXBUIIsBorddM@clustertraintracker.c1gsv4y.mongodb.net/?retryWrites=true&w=majority&appName=ClusterTrainTracker'; // Replace <password> with your actual password

async function connectToMongoDB() {
  const client = new MongoClient(uri, { 
    tlsAllowInvalidCertificates: true, 
    tlsAllowInvalidHostnames: true,
    serverSelectionTimeoutMS: 5000 
  });

  try {
    await client.connect();
    console.log('Connected to MongoDB successfully');
    return client;
  } catch (error) {
    console.error('Error connecting to MongoDB', error);
    process.exit(1);
  }
}

module.exports = connectToMongoDB;