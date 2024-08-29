import pika
import json
import time
import random
from pymongo import MongoClient
from geopy.distance import geodesic
from datetime import datetime, timezone
import geojson
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

timestamp = datetime.now(timezone.utc).isoformat()

# Load GeoJSON railway data
file_path = 'C:\\Users\\Lenovo\\OneDrive\\Desktop\\CW-Web-API-Data-Generator\\data\\hotosm_lka_railways_lines_geojson.geojson'

with open(file_path) as f:
    railway_data = geojson.load(f)

# Load train data from JSON file
with open('trains.json') as f:
    trains = json.load(f)

def find_nearest_point(train_position):
    """
    Finds the nearest point on the railway line to the given train position.
    """
    min_distance = float('inf')
    nearest_point = None
    
    for feature in railway_data['features']:
        for coord in feature['geometry']['coordinates']:
            point = (coord[1], coord[0])  # GeoJSON stores coordinates as [longitude, latitude]
            distance = geodesic(train_position, point).meters
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
                
    return nearest_point

def simulate_iot_data(train_id, train_name, route):
    """
    Simulate data from IoT devices attached to trains.
    Sends signals at one-minute intervals.
    """
    previous_position = route[0]
    
    for position in route[1:]:
        # Calculate the distance between the current position and the next position
        speed = random.uniform(30, 100)  # Random speed between 30 and 100 km/h
        distance_to_next_point = geodesic(previous_position[::-1], position[::-1]).meters
        
        # Calculate the time it would take to travel to the next point
        travel_time = distance_to_next_point / (speed * 1000 / 3600)  # Speed converted to m/s
        
        # If the travel time is less than a minute, skip to the next position
        if travel_time < 60:
            nearest_position = find_nearest_point(position[::-1])
            previous_position = position
        else:
            # Calculate the fraction of the distance to travel in one minute
            fraction = 60 / travel_time
            next_latitude = previous_position[1] + fraction * (position[1] - previous_position[1])
            next_longitude = previous_position[0] + fraction * (position[0] - previous_position[0])
            nearest_position = find_nearest_point((next_latitude, next_longitude))
            previous_position = (next_longitude, next_latitude)
        
        # Update timestamp for each iteration
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Simulate IoT data
        data = [
        {
            "train_id": train_id,
            "train_name": train_name,
            "latitude": nearest_position[0],
            "longitude": nearest_position[1],
            "timestamp": timestamp,
            "speed": speed,  # Use the calculated speed
            "signal_strength": random.uniform(0, 100)  # Random signal strength between 0 and 100%
        }
        ]
        
        # Send data to web API endpoint
        api_endpoint = "http://localhost:3001/api/gpsdata"  # Replace with your actual API endpoint
        response = requests.post(api_endpoint, json=data)
        if response.status_code == 201:
            print(f"Successfully sent IoT data: {data}")
        else:
            print(f"Failed to send data: {response.status_code}, {response.text}")
        time.sleep(60)  # Wait for one minute


def simulate_train_position(train_id, train_name, route):
    """
    Simulate the train position along the route.
    """
    print(f"Simulating train {train_name} (ID: {train_id}) on route")
    simulate_iot_data(train_id, train_name, route)

def run_simulations():
    """
    Run simulations for a random selection of trains concurrently.
    """
    all_train_ids = list(trains.keys())
    selected_train_ids = random.sample(all_train_ids, min(3, len(all_train_ids)))  # Select up to 3 trains

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(simulate_train_position, train_id, trains[train_id]['name'], trains[train_id]['route'])
                   for train_id in selected_train_ids]
        for future in as_completed(futures):
            try:
                future.result()  # Handle exceptions if any
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_simulations()
