from Options import FreeText, NumericOption, Toggle, DefaultOnToggle, Choice, TextChoice, Range, NamedRange, PerGameCommonOptions
from typing import Type
from typing import Type
from Options import FreeText, NumericOption, Toggle, DefaultOnToggle, Choice, TextChoice, Range, NamedRange, PerGameCommonOptions
# Object classes from AP that represent different types of options that you can create
from typing import Any
from Options import Option, OptionGroup, OptionSet

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value



####################################################################
# NOTE: At the time that options are created, Manual has no concept of the multiworld or its own world.
#       Options are defined before the world is even created.
#
# Example of creating your own option:
#
#   class MakeThePlayerOP(Toggle):
#       """Should the player be overpowered? Probably not, but you can choose for this to do... something!"""
#       display_name = "Make me OP"
#
#   options["make_op"] = MakeThePlayerOP
#
#
# Then, to see if the option is set, you can call is_option_enabled or get_option_value.
#####################################################################


# To add an option, use the before_options_defined hook below and something like this:
#   options["total_characters_to_win_with"] = TotalCharactersToWinWith
#
class Victims(OptionSet):
    """Which players are being linklinked?  If left empty, all of them!"""
    display_name = "LinkLink Players"

    @classmethod
    def get_option_name(cls, value) -> str:
        if value == []:
            return "Everybody"
        return ", ".join(sorted(value))


# This is called before any manual options are defined, in case you want to define your own with a clean slate or let Manual define over them
def before_options_defined(options: dict) -> dict:
    options["victims"] = Victims
    return options

# This is called after any manual options are defined, in case you want to see what options are defined or want to modify the defined options
def after_options_defined(options: dict) -> dict:
    return options

def before_option_groups_created(groups: dict[str, list[type[Option[Any]]]]) -> dict[str, list[type[Option[Any]]]]:
    return groups


def after_option_groups_created(groups: list[OptionGroup]) -> list[OptionGroup]:
    return groups
