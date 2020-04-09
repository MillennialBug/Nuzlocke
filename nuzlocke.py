from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import sqlite3
from time import time
import config

FILENAME = 'Nuzlocke-Overlay.png'
BASE_OVERLAY = r'overlay.png'
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT = ImageFont.truetype("Pokemon Solid.ttf", 50)
conn = sqlite3.connect('nuzlocke.db')
cur = conn.cursor()


def update():
    overlay = Image.open(BASE_OVERLAY, 'r').convert('RGBA')
    layer = Image.new('RGBA', overlay.size, WHITE + (0,))
    draw = ImageDraw.Draw(overlay)

    cur.execute('SELECT name, type FROM team WHERE team.active=? ORDER BY team.updated', ("Y",))
    rows = cur.fetchall()
    position = 1

    if rows is not None:
        if team_count() > 6:
            print('Too many Pokemon in team.')
            return

        for pkmn in rows:
            try:
                pokemon = Image.open(f'pkmn/{pkmn[1]}.png').convert('RGBA')
                layer.paste(pokemon, config.TEAM_POS[position])
                draw.text(config.NAME_POS[position], pkmn[0].capitalize(), WHITE, font=FONT)
                position += 1
            except FileNotFoundError:
                print(f'File not found. pkmn/{pkmn[1]}.png')
                conn.rollback()

    cur.execute('SELECT value FROM globals WHERE name=?', ('badges',))
    temp = cur.fetchone()
    draw.text(config.BADGES_POS, temp[0], WHITE, font=FONT)

    cur.execute('SELECT value FROM globals WHERE name=?', ('deaths',))
    temp = cur.fetchone()
    draw.text(config.DEATHS_POS, temp[0], WHITE, font=FONT)

    Image.alpha_composite(overlay, layer).save(FILENAME)


def increase_count(name):
    cur.execute('SELECT value FROM globals WHERE name=?', (name,))
    temp = cur.fetchone()
    total = int(temp[0]) + 1
    cur.execute('UPDATE globals SET value=? WHERE name=?', (total, name))


def team_count():
    cur.execute('SELECT COALESCE(COUNT(*),0) FROM team WHERE active=?', ('Y',))
    count = cur.fetchone()
    return int(count[0])


if __name__ == "__main__":

    cur.execute('CREATE TABLE IF NOT EXISTS team'
                '(id INTEGER PRIMARY KEY,'
                ' type TEXT NOT NULL,'
                ' name TEXT NOT NULL,'
                ' active TEXT,'
                ' caught REAL,'
                ' updated REAL)')
    cur.execute('CREATE TABLE IF NOT EXISTS globals'
                '(id INTEGER PRIMARY KEY,'
                ' name TEXT NOT NULL,'
                ' value TEXT NOT NULL)')
    cur.execute('SELECT value FROM globals where name=?', ('init',))
    init = cur.fetchone()
    if init is None:
        cur.execute('INSERT INTO globals (name, value) VALUES (?,?)', ('badges', '0'))
        cur.execute('INSERT INTO globals (name, value) VALUES (?,?)', ('deaths', '0'))
        cur.execute('INSERT INTO globals (name, value) VALUES (?,?)', ('init', 'Y'))
        conn.commit()

    while True:

        args = input('Enter a command... ').split()

        # if pokemon is caught, add to team table and set as inactive. Check if there is space in team to add
        # pokemon, if so, update active to Y
        if args[0] == 'catch':
            cur.execute('INSERT INTO team (type, name, active, caught) '
                        'VALUES (?,?,?,?)', (args[1].lower(), args[2].lower(), 'N', time()))
            if team_count() < 6:
                cur.execute('UPDATE team SET active=?, updated=? WHERE name=?', ('Y', time(), args[2].lower()))

        # increase badge count by 1
        elif args[0] == 'badge':
            increase_count('badges')

        # increase death count by 1 and set pokemon as inactive
        elif args[0] == 'death':
            increase_count('deaths')
            cur.execute('UPDATE team SET active=?, updated=? WHERE name=?', ('D', time(), args[1].lower()))

        # swaps first named pokemon for second one in the team
        elif args[0] == 'swap':
            cur.execute('UPDATE team SET active=?, updated=? WHERE name=?', ('N', time(), args[1].lower()))
            cur.execute('UPDATE team SET active=?, updated=? WHERE name=?', ('Y', time(), args[2].lower()))

        # evolves named pokemon. enter name first followed by the evolution
        elif args[0] == 'evolve':
            cur.execute('SELECT type FROM team WHERE name=?', (args[1].lower(),))
            row = cur.fetchone()
            if row[0] == 'eevee':
                cur.execute('UPDATE team SET type=? WHERE team.name=?', (config.EVOLVE[row[0]][args[2].lower()],
                                                                         args[1].lower()))
            else:
                cur.execute('UPDATE team SET type=? WHERE team.name=?', (config.EVOLVE[row[0]], args[1].lower()))

        # devolves named pokemon. mainly for debugging and crashes
        elif args[0] == 'devolve':
            cur.execute('UPDATE team SET type=? WHERE team.name=?', (args[2].lower(), args[1].lower()))

        # deletes a pokemon from the team table entirely. mainly for debugging but also for crashes.
        elif args[0] == 'remove':
            cur.execute('DELETE FROM team WHERE team.name=?', (args[1].lower(),))

        # resets the database to it's initial state
        elif args[0] == 'reset':
            cur.execute('DELETE FROM team')
            cur.execute('UPDATE globals SET value=?', (0,))

        # get a pokemon out of the box.
        elif args[0] == 'get':
            if team_count() < 6:
                cur.execute('UPDATE team SET active=? WHERE name=?', ('Y', args[1].lower()))

        # exits the program
        elif args[0] == 'exit':
            conn.close()
            exit()

        update()
        conn.commit()
