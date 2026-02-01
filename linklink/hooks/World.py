# Object classes from AP core, to represent an entire MultiWorld and this individual World that's part of it
import logging
import re
from worlds.AutoWorld import World
from BaseClasses import MultiWorld, CollectionState, Item
from typing import TYPE_CHECKING
from collections.abc import Iterator

from .Data import MAX_PLAYERS

# Object classes from Manual -- extending AP core -- representing items and locations that are used in generation
from ..Items import ManualItem
from ..Locations import ManualLocation

# Raw JSON data from the Manual apworld, respectively:
#          data/game.json, data/items.json, data/locations.json, data/regions.json
#
from ..Data import game_table, item_table, location_table, region_table

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value

# calling logging.info("message") anywhere below in this file will output the message to both console and log file
import logging

if TYPE_CHECKING:
    from .. import ManualWorld

########################################################################################
## Order of method calls when the world generates:
##    1. create_regions - Creates regions and locations
##    2. create_items - Creates the item pool
##    3. set_rules - Creates rules for accessing regions and locations
##    4. generate_basic - Runs any post item pool options, like place item/category
##    5. pre_fill - Creates the victory location
##
## The create_item method is used by plando and start_inventory settings to create an item from an item name.
## The fill_slot_data method will be used to send data to the Manual client for later use, like deathlink.
########################################################################################



# Use this function to change the valid filler items to be created to replace item links or starting items.
# Default value is the `filler_item_name` from game.json
def hook_get_filler_item_name(world: World, multiworld: MultiWorld, player: int) -> str | bool:
    return False

# Called before regions and locations are created. Not clear why you'd want this, but it's here. Victory location is included, but Victory event is not placed yet.
def before_create_regions(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after regions and locations are created, in case you want to see or modify that information. Victory location is included.
def after_create_regions(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to remove locations from the world
    locationNamesToRemove = [] # List of location names

    # Add your code here to calculate which locations to remove

    for region in multiworld.regions:
        if region.player == player:
            for location in list(region.locations):
                if location.name in locationNamesToRemove:
                    region.locations.remove(location)
    if hasattr(multiworld, "clear_location_cache"):
        multiworld.clear_location_cache()

# The item pool before starting items are processed, in case you want to see the raw item pool at that stage
def before_create_items_starting(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# The item pool after starting items are processed but before filler is added, in case you want to see the raw item pool at that stage
def before_create_items_filler(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    # Use this hook to remove items from the item pool
    itemNamesToRemove = [] # List of item names

    # Add your code here to calculate which items to remove.
    #
    # Because multiple copies of an item can exist, you need to add an item name
    # to the list multiple times if you want to remove multiple copies of it.

    for itemName in itemNamesToRemove:
        item = next(i for i in item_pool if i.name == itemName)
        item_pool.remove(item)

    return item_pool

    # Some other useful hook options:

    ## Place an item at a specific location
    # location = next(l for l in multiworld.get_unfilled_locations(player=player) if l.name == "Location Name")
    # item_to_place = next(i for i in item_pool if i.name == "Item Name")
    # location.place_locked_item(item_to_place)
    # item_pool.remove(item_to_place)

# The complete item pool prior to being set for generation is provided here, in case you want to make changes to it
def after_create_items(item_pool: list[ManualItem], world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

def replace_nothings(world: World, multiworld: MultiWorld, player: int):
    # Remove "Nothing" items and replace them with filler items from other players
    item_pool = [i for i in multiworld.itempool if i.player == player]
    my_item_count = len([i for i in item_pool if i.player == player])
    location_count = len(multiworld.get_locations(player))
    unfilled_count = len(multiworld.get_unfilled_locations(player))

    filler_blacklist = ["Manual_LinkLink_Silasary"]
    victims = get_victims(multiworld, player)
    victims = [v for v in victims if v != player and multiworld.worlds[v].game not in filler_blacklist]  # Only include players with filler items

    other_player = None
    for item in [i for i in item_pool.copy() if i.name == "Nothing" and i.player == player]:
        item_pool.remove(item)

    my_item_count = len([i for i in item_pool if i.player == player])
    needed = location_count - my_item_count
    for _ in range(needed):
        if other_player is None:
            queue = iter(v for v in victims if v != player)
            other_player = next(queue)

        try:
            filler = world.multiworld.worlds[other_player].create_filler()
            if filler is None:
                raise Exception(f"Unable to create filler for {multiworld.player_name[other_player]}")
            multiworld.itempool.append(filler)
            multiworld.itempool.remove(item)
        except Exception as e:
            logging.error(f"Error creating filler for {multiworld.player_name[other_player]}: {e}")
            victims.remove(other_player)
            queue = iter(v for v in victims if v != player)
            if not victims:
                break
        other_player = next(queue, None)

# Called before rules for accessing regions and locations are created. Not clear why you'd want this, but it's here.
def before_set_rules(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after rules for accessing regions and locations are created, in case you want to see or modify that information.
def after_set_rules(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to modify the access rules for a given location

    def Example_Rule(state: CollectionState) -> bool:
        # Calculated rules take a CollectionState object and return a boolean
        # True if the player can access the location
        # CollectionState is defined in BaseClasses
        return True

    ## Common functions:
    # location = world.get_location(location_name, player)
    # location.access_rule = Example_Rule

    ## Combine rules:
    # old_rule = location.access_rule
    # location.access_rule = lambda state: old_rule(state) and Example_Rule(state)
    # OR
    # location.access_rule = lambda state: old_rule(state) or Example_Rule(state)

# The item name to create is provided before the item is created, in case you want to make changes to it
def before_create_item(item_name: str, world: World, multiworld: MultiWorld, player: int) -> str:
    return item_name

# The item that was created is provided after creation, in case you want to modify the item
def after_create_item(item: ManualItem, world: World, multiworld: MultiWorld, player: int) -> ManualItem:
    return item

# This method is run towards the end of pre-generation, before the place_item options have been handled and before AP generation occurs
def before_generate_basic(world: World, multiworld: MultiWorld, player: int) -> list:
    pass

# This method is run at the very end of pre-generation, once the place_item options have been handled and before AP generation occurs
def after_generate_basic(world: "ManualWorld", multiworld: MultiWorld, player: int):
    victims = get_victims(multiworld, player)
    players_digits = len(str(MAX_PLAYERS))

    unplaced_items = [i for i in multiworld.itempool if i.location is None]
    for item_data in item_table:
        if 'linklink' in item_data:
            logging.debug(repr(item_data))
            linklink: dict[str, list[str]] = item_data['linklink']
            item_count = item_data['count']
            digit = len(str(item_count + 1))
            for i in range(1, item_count + 1):
                any_placed = False
                n = 1
                for j in range(1, multiworld.players + 1):
                    if j == player or j not in victims:
                        continue
                    placed = False
                    location_name = f"{item_data['name']} {str(i).zfill(digit)} Player {str(n).zfill(players_digits)}"
                    location = multiworld.get_location(location_name, player)
                    if location is None:
                        continue
                    if multiworld.worlds[j].game not in linklink:
                        logging.debug(f"Game {multiworld.worlds[j].game} not in linklink for {item_data['name']}")
                        continue
                    location.ll_item_name = item_data['name']
                    options = [item for item in unplaced_items if item.name in linklink[multiworld.worlds[j].game] and item.player == j]
                    options.sort(key=lambda x: linklink[multiworld.worlds[j].game].index(x.name))
                    if i == 1 and len(options) == 0:
                        logging.warning(f"No options for {item_data['name']} {i} for {multiworld.player_name[j]} ({multiworld.worlds[j].game})")

                    for item in options:
                        if placed:
                            break
                        location.place_locked_item(item)
                        unplaced_items.remove(item)
                        multiworld.itempool.remove(item)
                        n += 1
                        # print(f"Placed {item.name} in {location.name} for {multiworld.player_name[j]} ({multiworld.worlds[j].game})")
                        placed = True
                        any_placed = True
                        break
                if not any_placed:
                    item = next(item for item in unplaced_items if item.name == item_data['name'] and item.player == player)
                    logging.info(f'Removing surplus {item.name}')
                    multiworld.itempool.remove(item)
                    unplaced_items.remove(item)
            if not getattr(multiworld, 'generation_is_fake', False):
                for location in multiworld.get_unfilled_locations(player):
                    if location.name.startswith(f"{item_data['name']} "):
                        location.parent_region.locations.remove(location)
                        # remove_nothing()
    replace_nothings(world, multiworld, player)



def get_victims(multiworld: MultiWorld, player: int) -> set[int]:
    victims: set = get_option_value(multiworld, player, "victims")

    if len(victims) == 0:
        victims = set(range(1, multiworld.players + 1))
    else:
        id_for_names = {multiworld.player_name[i]: i for i in range(1, multiworld.players + 1)}
        victims = set([id_for_names[v] for v in victims])
    return victims



# This is called before slot data is set and provides an empty dict ({}), in case you want to modify it before Manual does
def before_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called after slot data is set and provides the slot data at the time, in case you want to check and modify it after Manual is done with it
def after_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called right at the end, in case you want to write stuff to the spoiler log
def before_write_spoiler(world: World, multiworld: MultiWorld, spoiler_handle) -> None:
    pass

# This is called when you want to add information to the hint text
def before_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    from itertools import groupby
    items = [loc.item for loc in multiworld.get_filled_locations() if loc.item is not None and loc.item.player == player]
    items.extend(multiworld.precollected_items.get(player, []))
    items = [i for i in items if i.advancement]

    groups: dict[str,list] = {}
    def keyfunc(i):
        return i.name

    data = sorted(items, key=keyfunc)
    for k, g in groupby(data, key=keyfunc):
        if k not in groups.keys():
            groups[k] = list(g)

    if player not in hint_data:
        hint_data.update({player: {}})

    iterators: dict[str, dict[str, Iterator]] = {}
    next_item: dict[str, dict[str, Item|None]] = {}
    # hintsdone: dict[str, list[str]] = {}
    for location in multiworld.get_locations(player):
        if not location.address:
            continue

        if location.parent_region is not None and location.parent_region.name == "Free Items":
            continue

        item_name = location.ll_item_name  #re.split(r"\d+", location.name)[0].strip()
        item_name = item_name.strip()
        p_num = str(location.item.player)
        if p_num not in iterators.keys():
            iterators[p_num] = {}
            next_item[p_num] = {}
            # hintsdone[p_num] = []

        if next_item[p_num].get(item_name, None) is None or item_name not in iterators[p_num].keys():
            ll_keys = list(groups.get(item_name, []))
            world.random.shuffle(ll_keys)

            iterators[p_num][item_name] = iter(ll_keys)
            next_item[p_num][item_name] = next(iterators[p_num][item_name], None)

        current_item = next_item[p_num][item_name]
        if current_item is not None:
            if current_item.location is not None:
                hint_data[player][location.address] = f"{str(current_item.location)}"
            else:
                hint_data[player][location.address] = f"In {multiworld.player_name[player]}'s start inventory"
            pass
        # hintsdone[p_num].append(f"{rest.strip()}: {hint_data[player][location.address]}")
        next_item[p_num][item_name] = next(iterators[p_num][item_name], None)

def after_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    pass


def before_create_items_all(item_config: dict[str, int | dict], world: World, multiworld: MultiWorld, player: int) -> dict[str, int | dict]:
    return item_config


def after_collect_item(world: World, state: CollectionState, Changed: bool, item: Item):
    pass


def after_remove_item(world: World, state: CollectionState, Changed: bool, item: Item):
    pass


def before_generate_early(world: World, multiworld: MultiWorld, player: int) -> None:
    """
    This is the earliest hook called during generation, before anything else is done.
    Use it to check or modify incompatible options, or to set up variables for later use.
    """
    pass


def hook_interpret_slot_data(world: World, player: int, slot_data: dict[str, Any]) -> dict[str, Any]:
    """
        Called when Universal Tracker wants to perform a fake generation
        Use this if you want to use or modify the slot_data for passed into re_gen_passthrough
    """
    return slot_data
