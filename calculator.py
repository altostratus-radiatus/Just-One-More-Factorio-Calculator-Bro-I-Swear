import re
import json

from ortools.init.python import init
from ortools.linear_solver import pywraplp

MAX_COST = 10000000
COST_PER_ITEM = 1
COST_PER_FLUID = 40 * 100 / 25000
COST = {'item': COST_PER_ITEM, 'fluid': COST_PER_FLUID}
SPECIAL_PRODUCTS_COST = {
    'guano': COST_PER_ITEM,
    'mova': COST_PER_ITEM,
    'crude-oil': COST_PER_FLUID,
    'raw-gas': COST_PER_FLUID,
    'tar': COST_PER_FLUID,
    'steam': COST_PER_FLUID
}

DEFAULT_PRODUCTIVITY = 0.6
# Molecular assembler and particle accelerator lag behind in building tier
PRODUCTIVITY_FOR_CATEGORY = {
    'nano': 0.4,
    'pa': 0.4,
    'mining': 0.5
}

class DefaultDict(dict):
    def __init__(self, default_factory):
        self.default_factory = default_factory
    def __missing__(self, key):
        self[key] = self.default_factory(key)
        return self[key]

def main():
    # Create the linear solver with the GLOP backend.
    solver = pywraplp.Solver.CreateSolver("GLOP")
    if not solver:
        print("Could not create solver GLOP")
        return

    with open('technologies.json') as f:
        technologies = json.load(f)

    with open('recipes.json') as f:
        recipes = json.load(f)

    infinity = solver.infinity()
    variables = DefaultDict(lambda v: solver.NumVar(0, MAX_COST, v))
    constraints = {}
    produced_variables = set()
    for recipe_name, recipe in recipes.items():
        logistics_cost = 0.0
        constraint = solver.Constraint(-infinity, infinity, recipe_name)
        constraints[recipe_name] = constraint
        for ingredient in recipe['ingredients']:
            variable = variables[ingredient['name']]
            constraint.SetCoefficient(variable, -ingredient['amount'])
            logistics_cost += ingredient['amount'] * COST[ingredient['type']]
        for product in recipe['products']:
            produced_variables.add(product['name'])
            variable = variables[product['name']]
            if 'amount' in product:
                final_amount = product['amount']
            else:
                final_amount = (product['amount_min'] + product['amount_max']) / 2
            if recipe['productivity']:
                if 'catalyst_amount' in product:
                    catalyst_amount = product['catalyst_amount']
                else:
                    catalyst_amount = 0
                if catalyst_amount > product['amount']:
                    raise Exception('Inscrutable are the ways of Factorio')
                productivity = PRODUCTIVITY_FOR_CATEGORY.get(recipe['category'], DEFAULT_PRODUCTIVITY)
                final_amount += productivity * (product['amount'] - catalyst_amount)
            final_amount *= product['probability']
            constraint.SetCoefficient(variable, final_amount + constraint.GetCoefficient(variable))
            # should the recipe cost increse with the number of products?
            # logistics_cost += final_amount * COST[ingredient['type']]
        constraint.SetUb(logistics_cost)

    for name, cost in SPECIAL_PRODUCTS_COST.items():
        variables[name].SetUb(cost)

    not_produced_variables = variables.keys() - SPECIAL_PRODUCTS_COST.keys() - produced_variables
    print(f'Couldn\'t find recipes for {len(not_produced_variables)} items')
    print(not_produced_variables)

    print("Number of variables =", solver.NumVariables())
    print("Number of constraints =", solver.NumConstraints())

    objective = solver.Objective()
    for name, count in technologies.items():
        science_pack = variables[name]
        objective.SetCoefficient(science_pack, count / 1000)
    for name, variable in variables.items():
        objective.SetCoefficient(variable, 0.001)
    objective.SetMaximization()

    # print(solver.ExportModelAsLpFormat(False).replace('\\', '').replace(',_', ','), sep='\n')

    print(f"Solving with {solver.SolverVersion()}")
    result_status = solver.Solve()
    if result_status != pywraplp.Solver.OPTIMAL:
        print("The problem does not have an optimal solution!")
        if result_status == pywraplp.Solver.FEASIBLE:
            print("A potentially suboptimal solution was found")
        else:
            print("The solver could not solve the problem.")
            return
    print(f"Problem solved in {solver.iterations():d} iterations")

    print("Solution:")
    solution_values = {name: variable.solution_value() for name, variable in variables.items()}
    for name in technologies:
        print(name, ' = ', solution_values[name])

    flow_values = {recipe_name: constraints[recipe_name].dual_value() for recipe_name in recipes}
    
    bloody_expensive = 0
    for name, cost in solution_values.items():
        if cost == MAX_COST:
            bloody_expensive += 1
            # print('Bloody expensive: ', name)
    print('Bloody expensive items: ', bloody_expensive)

    small_potatoes = 0
    for name, cost in solution_values.items():
        if cost == 0:
            small_potatoes += 1
            # print('Small potato: ', name)
    print('Small potatoes: ', small_potatoes)

    with open('solutions.json', 'w') as f:
        json.dump(solution_values, f, indent=1)
    with open('flow_values.json', 'w') as f:
        json.dump(flow_values, f, indent=1)


if __name__ == "__main__":
    init.CppBridge.init_logging("calculator.py")
    cpp_flags = init.CppFlags()
    cpp_flags.stderrthreshold = True
    cpp_flags.log_prefix = False
    init.CppBridge.set_flags(cpp_flags)
    main()
