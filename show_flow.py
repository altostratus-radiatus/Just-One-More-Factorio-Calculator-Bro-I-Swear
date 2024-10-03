import json
import sys

if __name__=="__main__":
    with open('recipes.json') as f:
        recipes = json.load(f)
    with open('solutions.json', 'r') as f:
        solution_values = json.load(f)
    with open('flow_values.json', 'r') as f:
        flow_values = json.load(f)

    if len(sys.argv) != 2:
        print('Requires argument')
        exit()
    show_flow_for = sys.argv[1]

    print(show_flow_for, 'cost =', solution_values[show_flow_for])
    print('As ingredient')
    for recipe_name, recipe in recipes.items():
        for ingredient in recipe['ingredients']:
            if ingredient['name'] == show_flow_for:
                print('Flow:', flow_values[recipe_name], '  Recipe:', recipe_name, 'in', recipe['category'])
                break
    print('As product')
    for recipe_name, recipe in recipes.items():
        for product in recipe['products']:
            if product['name'] == show_flow_for:
                print('Flow:', flow_values[recipe_name], '  Recipe:', recipe_name, 'in', recipe['category'])
                for ingredient in recipe['ingredients']:
                    print(f"{ingredient['name']} = {ingredient['amount']} x {solution_values[ingredient['name']]}", end ='   ')
                print()
                break