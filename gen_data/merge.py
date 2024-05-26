import json
with open("object_info_new.json", 'r') as file:
    data1 = json.load(file)
with open("object_info_new_second.json", 'r') as file:
    data2 = json.load(file)
results = data1
for obj, places in data2.items():
    if obj not in results.keys():
        results[obj] = places
    else:
        for place in places:
            if place not in results[obj]:
                print(place)
                results[obj].append(place)
with open("available_places.json", 'w') as file:
    json.dump(results, file, indent=4)