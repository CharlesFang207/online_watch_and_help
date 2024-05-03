import pickle
import json
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--picklefile", type=str, default="", help="pickle file to switch")
parser.add_argument("--jsonfile", type=str, default="", help="json file to save")

if __name__ == "__main__":
    args = parser.parse_args()
    pickle_path = os.path.join(os.getcwd(), args.picklefile)
    # Load data from pickle file
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)

    # Convert data to JSON
    json_data = json.dumps(data)

    # Write JSON data to a file
    json_path = os.path.join(os.getcwd(), args.jsonfile)
    with open(json_path, 'w') as f:
        f.write(json_data)