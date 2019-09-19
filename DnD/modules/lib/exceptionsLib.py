class DnDError(Exception):
    pass


class LowOnResource(DnDError):
    def __init__(self, resource):
        self.resource = resource

    def __str__(self):
        formatstr = 'You have no {rs} remaining.'
        return formatstr.format(rs=self.resource.name)


class OutOfItems(DnDError):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        formatstr = 'You have no {item}s remaining.'
        return formatstr.format(item=self.name)


class SpellError(DnDError):
    pass


class OutOfSpells(SpellError):
    def __init__(self, character, spell):
        self.character = character
        self.spell = spell

    def __str__(self):
        formatstr = '{char} has no spell slots of level {lv} remaining.'
        return formatstr.format(char=self.character.name,
                                lv=(self.spell if isinstance(self.spell, int)
                                    else self.spell.level))


class OverflowSpells(SpellError):
    def __init__(self, character, spell):
        self.character = character
        self.spell = spell

    def __str__(self):
        formatstr = '{char} has full spell slots of level {lv} already.'
        return formatstr.format(char=self.character.name, lv=self.spell.level)


class NotARitualError(SpellError):
    pass


class CharacterDead(DnDError):
    pass