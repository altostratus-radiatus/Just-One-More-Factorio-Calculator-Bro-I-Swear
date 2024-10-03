local default_zero = {
    __index = function(t, k) return 0 end
}
local total_remaining_science = {}
setmetatable(total_remaining_science, default_zero)
for _, tech in pairs(game.player.force.technologies) do
    if tech.enabled and not tech.researched then
        for _, ingredient in pairs(tech.research_unit_ingredients) do
            total_remaining_science[ingredient.name] = total_remaining_science[ingredient.name] + tech.research_unit_count * ingredient.amount
        end
    end
end
game.write_file('technologies.json', game.table_to_json(total_remaining_science))

local modules = game.get_filtered_item_prototypes{{filter="type", type="module"}}
local limitations_list = modules['productivity-module'].limitations
local limitations = {}
for _, name in ipairs(limitations_list) do
    limitations[name] = true
end
local recipes = {}
for name, recipe in pairs(game.player.force.recipes) do
    if recipe.enabled and not name:find("^deadlock%-stack") and not name:find("pyvoid") then
        recipes[name] = {
            ingredients=recipe.ingredients,
            products=recipe.products,
            category=recipe.category,
            energy=recipe.energy,
            productivity=limitations[name] or false
        }
    end
end
local launchable_items = game.get_filtered_item_prototypes{{filter="has-rocket-launch-products"}}
for name, item in pairs(launchable_items) do
    recipes[name .. '-launch'] = {
        ingredients={{type="item", amount=1, name=item.name}, {type="item", amount=3, name="rocket-part"}},
        products=item.rocket_launch_products,
        category='rocket-launch',
        energy=0,
        productivity=false
    }
end
local fuels = game.get_filtered_item_prototypes{{filter="burnt-result"}}
for name, fuel in pairs(fuels) do
    if not name:find("^deadlock%-stack") and not name:find("^ee%-") then
        recipes[name .. '-burn'] = {
            ingredients={{type="item", amount=1, name=fuel.name}},
            products={{type="item", amount=1, probability=1, name=fuel.burnt_result.name}},
            category='burnt-fuel',
            energy=0,
            productivity=false
        }
    end
end
local minables = game.get_filtered_entity_prototypes{{filter="type", type="resource"}, {filter="minable", mode="and"}, {filter="autoplace", mode="and"}}
for name, minable in pairs(minables) do
    local minable_properties = minable.mineable_properties
    assert(minable_properties.minable, 'minable is not mineable')
    if minable_properties.products and #minable_properties.products > 0 then
        local recipe = {
            energy=minable_properties.mining_time,
            productivity=true,
            category='mining',
            ingredients={},
            products=minable_properties.products
        }
        if minable_properties.required_fluid then
            recipe.ingredients={{type="fluid", amount=minable_properties.fluid_amount / 10, name=minable_properties.required_fluid}}
        end
        recipes['mine-' .. name] = recipe
    end
end
local offshore_pumps = game.get_filtered_entity_prototypes{{filter="type", type="offshore-pump"}}
for name, pump in pairs(offshore_pumps) do
    recipes[name .. '-pumping'] = {
        energy=0,
        productivity=false,
        ingredients={},
        products={{type="fluid", amount=1, name=pump.fluid.name, probability=1}},
        category='pumping'
    }
end
game.write_file('recipes.json', game.table_to_json(recipes))