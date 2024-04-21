import entsoe_multiple_preprocess as emp

for key in emp.loads_from_json:
    print(key)
    print(emp.loads_from_json[key])

for key in emp.gens_from_json:
    print(key)
    print(emp.gens_from_json[key])