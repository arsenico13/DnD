import enum
import tkinter as tk
from typing import Optional

import dndice as d

import lib.abilitiesLib as abil
import lib.characterLib as char
import lib.components as gui


class DisplayMode(enum.Enum):
    """How the abilities should be displayed, in ROW x COLUMN order."""
    SIX_BY_ONE = '6x1'
    THREE_BY_TWO = '3x2'
    TWO_BY_THREE = '2x3'
    ONE_BY_SIX = '1X6'


class AbilityDisplay(gui.Section):
    def __init__(self, parent, ability: 'abil.Ability', mode: DisplayMode,
                 advantage: gui.AdvantageChooser, display: gui.RollDisplay, **kwargs):
        super().__init__(parent, **kwargs)
        self.ability = ability
        self.advantage = advantage
        self.display = display
        self.check = tk.Button(self.f, width=4, text=ability.abbreviation,
                               command=self.roll_check)
        self.score = gui.NumericEntry(self.f, width=4, callback=self.update,
                                      start=self.ability.score)
        self.modifier = tk.Label(self.f, width=2)
        self._display_modifier()
        self.save = gui.ProficientButton(self.f, 'SAVE', width=4,
                                         command=self.roll_save)
        self.check.grid(row=0, column=0)
        if mode == DisplayMode.SIX_BY_ONE:
            self.score.grid(row=0, column=1)
            self.modifier.grid(row=0, column=2)
            self.save.grid(row=0, column=3)
        else:
            self.score.grid(row=1, column=0)
            self.modifier.grid(row=2, column=0)
            self.save.grid(row=3, column=0)

    def update(self, score):
        self.ability.score = score
        self._display_modifier()

    def _display_modifier(self):
        self.modifier['text'] = '{:+d}'.format(self.ability.modifier)

    def roll(self, extra: Optional[d.core.EvalTree] = None):
        expr = self.advantage.d20_roll()
        expr += d.compile(self.ability.modifier)
        if extra:
            expr += extra
        self.display.set(expr)

    def roll_check(self):
        self.roll()

    def roll_save(self):
        self.roll()

    def update_view(self):
        self.score.set(self.ability.score)
        self._display_modifier()


class OwnedAbilityDisplay(AbilityDisplay):
    def __init__(self, parent, character: 'char.Character', ability: 'abil.Ability',
                 mode: DisplayMode, advantage: gui.AdvantageChooser, display: gui.RollDisplay,
                 **kwargs):
        super().__init__(parent, ability, mode, advantage, display, **kwargs)
        self.owner = character
        self.save.proficient = self.ability.name in self.owner.saves

    def roll_save(self):
        value, roll = self.owner.ability_save(self.ability.name,
                                              self.advantage.advantage,
                                              self.advantage.disadvantage)
        self.display.set(roll)

    def roll_check(self):
        value, roll = self.owner.ability_check(self.ability.name,
                                               adv=self.advantage.advantage,
                                               dis=self.advantage.disadvantage)
        self.display.set(roll)


class StaticAbilityDisplay(gui.Section):
    def __init__(self, container, ability: 'abil.Ability', mode: DisplayMode):
        super().__init__(container)
        self.ability = ability
        self.name = tk.Label(self.f, text=self.ability.abbreviation)
        self.name.grid(row=0, column=0)
        self.numbers = tk.Label(self.f)
        if mode == DisplayMode.SIX_BY_ONE:
            self.numbers.grid(row=0, column=1)
        else:
            self.numbers.grid(row=1, column=0)
        self.update_view()

    def update_view(self):
        numbers = '{s} ({m:+d})'.format(s=self.ability.score, m=self.ability.modifier)
        self.numbers['text'] = numbers


class BasicAbilityDisplay(gui.Section):
    def __init__(self, container, ability: abil.Ability, mode: DisplayMode, **kwargs):
        super().__init__(container, **kwargs)
        self.ability = ability
        self.name = tk.Label(self.f, text=self.ability.abbreviation)
        self.name.grid(row=0, column=0)
        self.entry = gui.NumericEntry(self.f, self.ability.score, self.update, 4)
        self.modifier = tk.Label(self.f, width=2)
        self._display_modifier()
        if mode == DisplayMode.SIX_BY_ONE:
            self.entry.grid(0, 1)
            self.modifier.grid(row=0, column=2)
        else:
            self.entry.grid(1, 0)
            self.modifier.grid(row=2, column=0)

    def update(self, score):
        self.ability.score = score
        self._display_modifier()

    def update_view(self):
        self.entry.set(self.ability.score)
        self._display_modifier()

    def _display_modifier(self):
        self.modifier['text'] = '{:+d}'.format(self.ability.modifier)


class AbilitiesDisplay(gui.Section):
    def __init__(self, container, abilities: 'abil.Abilities', mode: DisplayMode,
                 adv: gui.AdvantageChooser = None, display: gui.RollDisplay = None,
                 **kwargs):
        super().__init__(container, **kwargs)
        self.abilities = abilities
        self.advantage = adv
        self.rollDisplay = display
        self.displays = self._construct_displays(mode)

        def calculate_pos(index):
            if mode == DisplayMode.SIX_BY_ONE:
                return index, 0
            if mode == DisplayMode.TWO_BY_THREE:
                # Row 1: STR DEX CON   Row 2: INT WIS CHA
                return index // 3, index % 3
            if mode == DisplayMode.THREE_BY_TWO:
                # Column 1: STR DEX CON   Column 2: INT WIS CHA
                return index % 3, index // 3
            if mode == DisplayMode.ONE_BY_SIX:
                return 0, index
            raise TypeError('Mode argument is incorrect')

        for i, display in enumerate(self.displays):
            display.grid(*calculate_pos(i))

    def _construct_displays(self, mode):
        return [AbilityDisplay(self.f, self.abilities[name], mode,
                               self.advantage, self.rollDisplay)
                for name in abil.AbilityName]

    def update_view(self):
        for display in self.displays:
            display.update_view()


class StaticAbilitiesDisplay(AbilitiesDisplay):
    def __init__(self, container, abilities: 'abil.Abilities', mode: DisplayMode, **kwargs):
        super().__init__(container, abilities, mode, **kwargs)

    def _construct_displays(self, mode):
        return [StaticAbilityDisplay(self.f, self.abilities[name], mode)
                for name in abil.AbilityName]


class BasicAbilitiesDisplay(AbilitiesDisplay):
    def __init__(self, container, abilities: 'abil.Abilities', mode: DisplayMode, **kwargs):
        super().__init__(container, abilities, mode, **kwargs)

    def _construct_displays(self, mode):
        return [BasicAbilityDisplay(self.f, self.abilities[name], mode)
                for name in abil.AbilityName]


class OwnedAbilitiesDisplay(AbilitiesDisplay):
    def __init__(self, container, character: 'char.Character', abilities: 'abil.Abilities',
                 mode: DisplayMode, adv: gui.AdvantageChooser, display: gui.RollDisplay,
                 **kwargs):
        self.owner = character
        super().__init__(container, abilities, mode, adv, display, **kwargs)

    def _construct_displays(self, mode):
        return [OwnedAbilityDisplay(self.f, self.owner, self.abilities[name], mode,
                                    self.advantage, self.rollDisplay)
                for name in abil.AbilityName]


class Module(OwnedAbilitiesDisplay):
    def __init__(self, container, character: 'char.Character', adv: gui.AdvantageChooser,
                 output: gui.RollDisplay):
        self.owner = character
        super().__init__(container, character, character.abilities, DisplayMode.SIX_BY_ONE, adv,
                         output, pady=5)


class Main(gui.MainModule):
    def __init__(self, window: tk.Tk):
        self.adv = gui.AdvantageChooser(window)
        self.display = gui.RollDisplay(window)

        def creator(character: 'char.Character'):
            return Module(window, character, self.adv, self.display)

        super().__init__(window, creator)

        self.adv.grid(1, 0)
        self.display.grid(2, 0)


if __name__ == '__main__':
    win = gui.MainWindow()
    Main(win).run()
