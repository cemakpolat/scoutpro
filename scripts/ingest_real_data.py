import os
import json
import csv
import argparse
import requests

def parse_statsbomb_csv(filepath):
    print(f"Parsing StatsBomb CSV: {filepath}")
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)
    return events

def parse_opta_json(filepath):
    print(f"Parsing Opta XML/JSON: {filepath}")
    # Placeholder for reading Opta data. In this project, it could be XML or JSON.
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Navigate to the events array in F24 payload
            if isinstance(data, dict):
                if 'Games' in data and 'Game' in data['Games'] and 'Event' in data['Games']['Game']:
                    return data['Games']['Game']['Event']
                elif 'match' in data and 'liveData' in data['match'] and 'lineup' in data['match']['liveData']:
                    pass # Placeholder for other opta formats like F9
                    
            # Return raw data if it can't be introspected as a list of events
            if isinstance(data, list):
                return data
            return [data] # Fallback wraparound for processing 
    except Exception as e:
        print(f"Error parse_opta_json: {e}")
        return []

def send_to_endpoints(data, endpoint_url, match_id="3946949", source="opta"):
    # Fix the endpoint URL if it uses placeholder format
    if "{match_id}" in endpoint_url:
        endpoint_url = endpoint_url.replace("{match_id}", str(match_id))
    elif not endpoint_url.endswith("/" + str(match_id)):
        endpoint_url = f"{endpoint_url.rstrip('/')}/{match_id}"
        
    print(f"Sending {len(data)} records to {endpoint_url}")
    # Sample chunked send
    chunk_size = 100
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        try:
            response = requests.post(endpoint_url, json={"events": chunk, "source": source})
            print(f"Chunk {i}-{i+len(chunk)}: Status {response.status_code}")
        except Exception as e:
            print(f"Failed to send to {endpoint_url}: {e}")
            continue

def main():
    parser = argparse.ArgumentParser(description="Ingest Opta/StatsBomb data")
    parser.add_argument("--source", type=str, required=True, choices=["opta", "statsbomb"], help="Data source type")
    parser.add_argument("--filepath", type=str, required=True, help="Path to data file")
    parser.add_argument("--endpoint", type=str, default="http://localhost:8006/api/v2/ingestion/events/{match_id}", help="Ingestion endpoint URL")
    parser.add_argument("--match_id", type=str, default="3946949", help="Match ID")

    args = parser.parse_args()

    if not os.path.exists(args.filepath):
        print(f"File not found: {args.filepath}")
        return
        
    if args.source == "statsbomb":
        data = parse_statsbomb_csv(args.filepath)
        send_to_endpoints(data, args.endpoint, args.match_id, args.source)
    elif args.source == "opta":
        data = parse_opta_json(args.filepath)
        send_to_endpoints(data, args.endpoint, args.match_id, args.source)

if __name__ == "__main__":
    main()
