import googlemaps
import geojson
import time
from datetime import datetime, timedelta
import json
import polyline
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Google Maps client
gmaps = googlemaps.Client(key='AIzaSyCZx6VOP5bywLQx1vY8JjPX-YCFV8E9JZA')

# Load the GeoJSON file containing train routes
with open('SLRailwayRoutes.geojson', encoding='utf-8') as f:
    routes = geojson.load(f)

def get_route(origin, destination):
    """Get the route between two points using Google Maps API."""
    print(f"Requesting route from {origin} to {destination}")
    try:
        directions_result = gmaps.directions(
            origin=f"{origin['latitude']},{origin['longitude']}",
            destination=f"{destination['latitude']},{destination['longitude']}",
            mode="transit",
            transit_mode="rail",
            units="metric"
        )
        if not directions_result:
            print("No directions found using rail. Trying without transit mode...")
            directions_result = gmaps.directions(
                origin=f"{origin['latitude']},{origin['longitude']}",
                destination=f"{destination['latitude']},{destination['longitude']}",
                mode="driving",
                units="metric"
            )
            if not directions_result:
                print("No directions found even with driving mode.")
                return []

        print(f"Directions found: {directions_result}")
        polyline_str = directions_result[0]['overview_polyline']['points']
        return polyline.decode(polyline_str)
    
    except googlemaps.exceptions.ApiError as e:
        print(f"Google Maps API error: {e}")
        return []

def simulate_train_route(train_data, speed_kmph, start_time):
    """Simulate the train moving along the route at a certain speed."""
    train_id = train_data['properties']['route']
    origin_coords = train_data['geometry']['coordinates'][0]
    destination_coords = train_data['geometry']['coordinates'][-1]

    origin = {'latitude': origin_coords[1], 'longitude': origin_coords[0]}
    destination = {'latitude': destination_coords[1], 'longitude': destination_coords[0]}
    
    print(f"Simulating route: {train_id}")
    
    route = get_route(origin, destination)

    if not route:
        return None

    geojson_route = {
        "type": "Feature",
        "properties": {
            "train_id": train_id,
            "timestamps": [],
            "start_time": start_time.isoformat()
        },
        "geometry": {
            "type": "LineString",
            "coordinates": []
        }
    }
    
    # Convert speed to meters per minute
    speed_mpm = (speed_kmph * 1000) / 60
    
    current_time = start_time
    
    for i in range(len(route) - 1):
        start_point = route[i]
        end_point = route[i + 1]
        # Calculate the distance between points
        try:
            distance_matrix_response = gmaps.distance_matrix(
                origins=[start_point],
                destinations=[end_point],
                mode="walking"
            )
            print("Distance matrix response:", distance_matrix_response)  # Debug print
            
            distance = distance_matrix_response['rows'][0]['elements'][0]['distance']['value']
            travel_time = distance / speed_mpm
            geojson_route['geometry']['coordinates'].append([start_point[1], start_point[0]])
            geojson_route['properties']['timestamps'].append(current_time.isoformat())
            
            print(f"Train {train_id} moving from {start_point} to {end_point} at {current_time}.")
            
            time.sleep(0.1)  # Simulate the passage of one minute
            current_time += timedelta(minutes=1)
        
        except KeyError as e:
            print(f"KeyError: {e} - Response structure may have changed.")
            return None
        except Exception as e:
            print(f"Error while processing distance matrix response: {e}")
            return None
    
    # Add the final point and timestamp to the route
    geojson_route['geometry']['coordinates'].append([route[-1][1], route[-1][0]])
    geojson_route['properties']['timestamps'].append(current_time.isoformat())
    
    return geojson_route

def generate_train_data(output_file, num_simultaneous_trains=5):
    """Generate train tracking data for multiple trains concurrently."""
    trains_data = []
    start_time = datetime.now()
    
    with ThreadPoolExecutor(max_workers=num_simultaneous_trains) as executor:
        futures = [
            executor.submit(simulate_train_route, train, TRAIN_SPEED_KMPH, start_time)
            for train in routes['features']
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                trains_data.append(result)
    
    if trains_data:
        with open(output_file, 'w', encoding='utf-8') as f:
            geojson.dump(geojson.FeatureCollection(trains_data), f)
        print(f"Data written to {output_file}")
    else:
        print("No data to write.")

# Configuration
TRAIN_SPEED_KMPH = 160  # Adjust speed as needed
OUTPUT_FILE = 'train_tracking_data.geojson'

# Generate the train data with up to 5 trains running simultaneously
generate_train_data(OUTPUT_FILE, num_simultaneous_trains=10)