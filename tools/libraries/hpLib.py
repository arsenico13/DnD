from math import ceil

from dndice import basic

import abilitiesLib as abil
import characterLib as char
import resourceLib as res
from exceptionsLib import LowOnResource
from interface import DataInterface
from settingsLib import RestLengths, HealingMode


class HP:
    def __init__(self, jf: DataInterface, character: 'char.Character'):
        self.owner = character
        self.record = jf
        self.hd = {size: HD(self.record.cd('/' + size), size, character)
                   for size in self.record.get('/HD')}

    @property
    def current(self):
        return self.record.get('/current')

    @current.setter
    def current(self, value):
        if isinstance(value, int):
            self.record.set('/current', value)
        else:
            raise TypeError('Trying to set HP to not a number')

    @property
    def max(self):
        return self.record.get('/max')

    @max.setter
    def max(self, value):
        self.record.set('/max', value)

    @property
    def temp(self):
        return self.record.get('/temp')

    @temp.setter
    def temp(self, value):
        self.record.set('/temp', value)

    def change(self, amount):
        """Change the HP

        :param amount: A rollable amount
        :return: The actual change in HP
        """
        delta = basic(amount)
        if delta == 0:
            return 0
        if delta < 0:
            if abs(delta) > self.temp:
                # overflow beyond temp
                delta += self.temp
                self.temp = 0
                self.current += delta
                return delta
            else:
                # Temp absorbs it all
                self.temp += delta
                return 0
        else:
            # healing
            if self.current + delta > self.max:
                delta = self.max - self.current
            self.current += delta
            return delta

    def add_temp(self, amount):
        """Add some temp HP

        :param amount: A rollable amount
        :return: The actual change in HP (always 0 because temp HP is not real)
        """
        delta = basic(amount)
        if delta > self.temp:
            self.temp = delta
        return 0

    def rest(self, length):
        if length == RestLengths.LONG:
            if self.owner.settings.healing in (HealingMode.VANILLA, HealingMode.FAST):
                self.current = self.max
            self.temp = 0
        for size in self.hd.values():
            size.rest(length)


class HD(res.OwnedResource):
    def __init__(self, jf: DataInterface, size: str, character: 'char.Character'):
        super().__init__(jf, character=character)
        self.name = 'Hit Die'
        self.value = size
        self.recharge = RestLengths.LONG

    @property
    def maxnumber(self):
        return self.owner.classes.maxHD[self.value]

    def use(self, _):
        try:
            roll = super().use(1)
        except LowOnResource:
            return 0
        conmod = self.owner.abilities[abil.AbilityName.CON].modifier
        return roll + conmod if (roll + conmod > 1) else 1

    def rest(self, length):
        if length == RestLengths.LONG:
            if self.owner.settings.healing == HealingMode.FAST:
                self.reset()
            else:
                self.regain(ceil(self.maxnumber / 2))
        if length == RestLengths.SHORT:
            if self.owner.settings.healing == HealingMode.FAST:
                self.regain(ceil(self.maxnumber / 4))
