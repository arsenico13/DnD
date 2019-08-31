#! /usr/bin/env python3

import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../libraries')

import dndice as d

import tkUtility as util
import helpers as h
from dice import DiceRoll
import GUIbasics as gui
import interface as iface


def all_children(frame):
    return childrenrecursive(frame)


def childrenrecursive(current):
    l = []
    for c in current.winfo_children():
        l.extend(childrenrecursive(c))
    l.append(current)
    return l


class Monster:
    abilnames = ['Strength', 'Dexterity', 'Constitution', 'Intelligence',
                 'Wisdom', 'Charisma']
    def __init__(self, data):
        self.name = data['name']
        self.HP = int(d.basic(data['HP'], mode=d.Mode.from_string('average' if data.get('average') else 'normal')))
        self.maxHP = self.HP
        self.AC = data['AC']
        self.abilities = data['abilities']
        self.initiative = (h.d20_roll() +
                           h.modifier(data['abilities']['Dexterity']))
        self.saves = data.get('saves', {})

    def __lt__(self, other):
        return self.initiative < other.initiative

    def alterHP(self, amount):
        self.HP += d.basic(amount)
        self.HP = 0 if self.HP < 0 else self.maxHP if self.HP > self.maxHP else self.HP


class MonsterDisplay(gui.Section):
    def __init__(self, container, monster):
        gui.Section.__init__(self, container, pady=5, bd=2, relief='groove')

        self.creature = monster
        ###########
        self.infopanel = tk.Frame(self.f)
        ###########
        self.namesec = tk.Frame(self.infopanel)
        self.nameL = tk.Label(self.namesec, text=monster.name, font="Calibri 18")
        self.initL = tk.Label(self.namesec, text='Initiative:  ' + str(self.creature.initiative))
        ###########
        self.hpsec = tk.Frame(self.infopanel)
        self.deltaL = tk.Label(self.hpsec, text='Change in HP')
        self.delta = tk.Entry(self.hpsec)
        self.delta.bind('<Return>', lambda callback: self.change_HP)
        self.change = tk.Button(self.hpsec, text='Change', command=self.change_HP)
        ##########
        self.acsec = tk.Frame(self.infopanel)
        self.hpL = tk.Label(self.acsec,
                            text='HP:  ' + str(monster.HP),
                            font='Calibri 18')
        self.acL = tk.Label(self.acsec,
                            text='   AC:  ' + str(monster.AC),
                            font='Calibri 16')

        ###########
        self.abilsec = tk.Frame(self.infopanel)
        self.abilnames = [tk.Label(self.abilsec, text=name[:3].upper()) for name in Monster.abilnames]
        self.abils = [tk.Label(self.abilsec, text='{s} ({m})'.format(s=self.creature.abilities[name], m=h.modifier(self.creature.abilities[name]))) for name in Monster.abilnames]
        ###############
        self.attacksec = tk.Frame(self.f)
        self.attacknotresult = tk.Frame(self.attacksec)

        self.attackL = tk.Label(self.attacknotresult, text='Attack Modifiers')
        self.attack = tk.Entry(self.attacknotresult, width=15)
        self.damageL = tk.Label(self.attacknotresult, text='Damage')
        self.damage = tk.Entry(self.attacknotresult, width=15)
        self.damage.bind('<Return>', lambda event: self.do_attack())
        self.perform = tk.Button(self.attacknotresult, text='Attack',
                                 command=self.do_attack)
        self.advsec = tk.Frame(self.attacknotresult)
        self.advantage = tk.BooleanVar()
        self.disadvantage = tk.BooleanVar()
        self.hasAdvantage = tk.Checkbutton(self.advsec,
                                           text="Advantage?",
                                           variable=self.advantage)
        self.hasDisadvantage = tk.Checkbutton(self.advsec,
                                              text="Disadvantage?",
                                              variable=self.disadvantage)
        self.attackresult = tk.Label(self.attacksec)
        self.damageresult = tk.Label(self.attacksec)
        ###########
        self.draw_static()
        self.draw_dynamic()

    def __lt__(self, other):
        return self.creature < other.creature

    def draw_static(self):
        self.infopanel.grid(row=0, column=0)
        ########
        self.namesec.grid(row=0, column=0)
        self.nameL.grid(row=0, column=0, sticky='w')
        self.initL.grid(row=1, column=0, sticky='e')
        ####
        self.acsec.grid(row=0, column=1)
        self.hpL.grid(row=0, column=0, sticky='w')
        self.acL.grid(row=0, column=1, sticky='e')
        #####
        self.abilsec.grid(row=1, column=0)
        for i in range(6):
            self.abilnames[i].grid(row=(i//3)*2, column=i%3)
            self.abils[i].grid(row=(i//3)*2+1, column=i%3)
        #######
        self.hpsec.grid(row=1, column=1)
        self.deltaL.grid(row=0, column=0)
        self.delta.grid(row=1, column=0)
        self.change.grid(row=1, column=1)
        ########
        self.attacksec.grid(row=1, column=0)
        self.attacknotresult.grid(row=0, column=0)
        self.attackL.grid(row=0, column=0)
        self.attack.grid(row=0, column=1)
        self.advsec.grid(row=0, column=2)
        self.hasAdvantage.grid(row=0, column=0, sticky='w')
        self.hasDisadvantage.grid(row=1, column=0, sticky='w')
        self.damageL.grid(row=1, column=0)
        self.damage.grid(row=1, column=1)
        self.perform.grid(row=1, column=2)
        self.attackresult.grid(row=1, column=0)
        self.damageresult.grid(row=2, column=0)

    def draw_dynamic(self):
        self.hpL['text'] = 'HP:  ' + str(self.creature.HP)
        if (self.creature.HP <= 0):
            every = all_children(self.f)
            every.append(self.f)
            for w in every:
                w['bg'] = 'red'

    def change_HP(self):
        self.creature.alterHP(self.delta.get())
        self.draw_dynamic()

    def do_attack(self):
        adv = self.advantage.get()
        dis = self.disadvantage.get()
        attack = h.d20_roll(adv, dis)
        attack += d.compile(self.attack.get())
        attroll = d.verbose(attack)
        ###
        if (attack.is_critical()):
            attroll = 'Critical Hit'
            damresult = d.verbose(self.damage.get(), d.Mode.CRIT)
        elif (attack.is_fail()):
            attroll = 'Critical Miss'
            damresult = '0'
        else:
            damresult = d.verbose(self.damage.get())
        ###
        self.attackresult['text'] = 'Attack result: ' + attroll
        self.damageresult['text'] = 'Damage done: ' + damresult


class Character:
    def __init__(self, data):
        self.name = data['name']
        self.initiative = d.basic(data['init'])

    def __lt__(self, other):
        return self.initiative < other.initiative


class CharacterDisplay(gui.Section):
    def __init__(self, container, character):
        gui.Section.__init__(self, container)
        self.creature = character
        self.name = tk.Label(self.f, text=character.name, font="Calibri 18")
        self.init = tk.Label(self.f, text=character.initiative,
                             font="Calibri 14")
        self.draw_static()

    def draw_static(self):
        self.name.grid(row=0, column=0)
        self.init.grid(row=1, column=0)

    def __lt__(self, other):
        return self.creature < other.creature


class Builder:
    #this will create a popup window that allows you to create new monsters and
    #add them to the main window
    def __init__(self, data, parent, prevmonster=None):
        # self.master = master
        self.data = data
        self.parent = parent
        self.prevmonster = prevmonster
        self.win = tk.Toplevel()

        self.choosefile = tk.Button(self.win, text='Choose from file', command=self.pick_file)
        self.choosefile.grid(row=0, column=0)

        self.mainframe = tk.Frame(self.win, bd=2, relief='ridge')
        self.mainframe.grid(row=1, column=0)

        self.name = util.labeledEntry(self.mainframe, 'Enter name', 0, 0)

        self.ac = util.labeledEntry(self.mainframe, 'Enter AC', 2, 0)

        self.hp = util.labeledEntry(self.mainframe, 'Enter HP as valid roll', 4, 0)

        self.av = tk.BooleanVar()
        self.average = tk.Checkbutton(self.mainframe, text="Take average?",
                                      variable=self.av)
        self.average.grid(row=5, column=1)

        self.abil = tk.Frame(self.mainframe)
        self.abil.grid(row=6, column=0)
        abilities = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
        self.entries = []
        labels = []
        for (i, n) in enumerate(abilities):
            self.entries.append(util.labeledEntry(self.abil, n, (i // 3) * 2,
                                                  i % 3, width=4))

        self.resolve = tk.Button(self.mainframe,
                                 text='Finish',
                                 command=lambda: self.finish())
        self.resolve.grid(row=9, column=0)

        self.copy()

    def pick_file(self):
        self.mainframe.destroy()
        # self.choosefile.destroy()
        # self.filequery = util.labeledEntry(self.win, 'Monster Name', 0, 0)
        # self.average = tk.Checkbutton(self.win,
        #                               text="Take average\nvalue of HP?",
        #                               variable=self.av)
        # self.average.grid(row=1, column=1)
        # self.confirm = tk.Button(self.win, text='Load', command=self.load_file)
        # self.confirm.grid(row=2, column=0)
        d = os.path.abspath(iface.JSONInterface.OBJECTSPATH) + '/monster/'
        self.filename = filedialog.askopenfilename(initialdir=d, filetypes=[('monster file', '*.monster')])
        # print(self.filename)
        self.load_file()

    def load_file(self):
        base = iface.JSONInterface.OBJECTSPATH
        # filename = 'monster/' + h.clean(self.filequery.get().casefold()) + '.monster'
        filename = self.filename
        # if (os.path.isfile(base + filename)):
        if (os.path.isfile(filename)):
            interface = iface.JSONInterface(filename, isabsolute=True)
            self.data.update(interface.get('/'))
            # self.data.update({'average': self.av.get()})
            av = messagebox.askyesno(message='Take average HP?')
            self.data.update({'average': av})
            self.finish(fromfile=True)
        else:
            gui.ErrorMessage('That file does not exist. Check your spelling.')

    def copy(self):
        if (self.prevmonster):
            util.replaceEntry(self.name, self.prevmonster['name'])
            util.replaceEntry(self.ac, self.prevmonster['AC'])
            util.replaceEntry(self.hp, self.prevmonster['HP'])
            self.av.set(self.prevmonster['average'])
            for (i, a) in enumerate(Monster.abilnames):
                util.replaceEntry(self.entries[i],
                                  self.prevmonster['abilities'][a])

    def finish(self, fromfile=False):
        if (not fromfile):
            self.data.update({'name': self.name.get(), 'AC': self.ac.get(),
                              'HP': self.hp.get(), 'average': self.av.get(),
                              'abilities': {a: int(self.entries[i].get()) for (i, a) in enumerate(Monster.abilnames)}})
        self.parent.new_monster_finish()
        self.win.destroy()


class CharacterBuilder:
    def __init__(self, data, parent):
        self.win = tk.Toplevel()
        self.master = parent
        self.data = data
        self.master = parent
        self.name = util.labeledEntry(self.win, 'Character Name', 0, 0)
        self.initiative = util.labeledEntry(self.win, 'Initiative roll', 2, 0)
        self.quit = tk.Button(self.win, text='Finish', command=self.finish)
        self.quit.grid(row=4, column=0)

    def finish(self):
        self.data.update({'name': self.name.get(), 'init': self.initiative.get()})
        self.master.new_character_finish()
        self.win.destroy()


class main(gui.Section):
    def __init__(self, window):
        gui.Section.__init__(self, window, height=770, width=965)
        self.container.title('Combat Encounter')
        self.monsterdata = {}
        self.prevmonster = {}
        self.characterdata = {}
        self.frames = []
        self.addons = tk.Frame(self.f)
        self.buttons = tk.Frame(self.addons)
        self.newmonster = tk.Button(self.buttons, text='New Monster',
                                    command=self.new_monster_start)
        self.newcharacter = tk.Button(self.buttons, text='New Character',
                                      command=self.new_character_start)
        self.QUIT = tk.Button(self.buttons, text='Quit', command=self.quit)
        self.roller = DiceRoll(self.addons)
        self.draw()

    def draw(self):
        self.frames.sort(reverse=True)
        for (i, f) in enumerate(self.frames):
            f.grid(row=i%3, column=i//3)
        i = len(self.frames)
        self.addons.grid(row=i%3, column=i//3)
        self.roller.grid(row=0, column=0)
        self.buttons.grid(row=1, column=0)
        self.newmonster.grid(row=0, column=0)
        self.newcharacter.grid(row=0, column=1)
        self.QUIT.grid(row=0, column=2)

    def new_character_start(self):
        self.characterdata = {}
        CharacterBuilder(self.characterdata, self)

    def new_character_finish(self):
        c = Character(self.characterdata)
        self.frames.append(CharacterDisplay(self.f, c))
        self.draw()

    def new_monster_start(self):
        self.monsterdata = {}
        Builder(self.monsterdata, self, self.prevmonster)

    def new_monster_finish(self):
        self.prevmonster = self.monsterdata
        m = Monster(self.monsterdata)
        self.frames.append(MonsterDisplay(self.f, m))
        self.draw()

    def quit(self):
        self.container.destroy()


if (__name__ == '__main__'):
    iface.JSONInterface.OBJECTSPATH = os.path.dirname(os.path.abspath(__file__)) + '/../objects/'
    win = gui.MainWindow()
    app = main(win)
    app.pack()
    win.mainloop()
