import asyncio

from sqlalchemy import Column, String, Table, and_, select

from cloudbot import hook
from cloudbot.util import database

table = Table(
    'user_pers',
    database.metadata,
    Column('network', String, primary_key=True),
    Column('user', String, primary_key=True),
    Column('perk', String, primary_key=True)
)


def add_perk(db, conn, user, perk):
    db.execute(table.insert().values(
        network=conn.name.lower(), user=user.lower(), perk=perk.lower()
    ))
    db.commit()


def get_user_perks(db, conn, user):
    rows = db.execute(select([table.c.perk], and_(
        table.c.network == conn.name.lower(),
        table.c.user == user.lower(),
    ))).fetchall()

    return [row[0] for row in rows]


def check_perk(db, conn, user, perk) -> bool:
    return perk.lower() in get_user_perks(db, conn, user)


def del_perk(db, conn, user, perk):
    db.execute(table.delete().where(and_(
        table.c.network == conn.name.lower(),
        table.c.user == user.lower(),
        table.c.perk == perk.lower(),
    )))
    db.commit()


def clear_perks(db, conn, user):
    db.execute(table.delete().where(and_(
        table.c.network == conn.name.lower(),
        table.c.user == user.lower(),
    )))
    db.commit()


@hook.command('addperk', permissions=['manage_patron'])
def cmd_add_perk(db, conn, text, event):
    """<account> <perk> [perk2] ... - Add a patreon perk for a user's account

    :type db: sqlalchemy.orm.Session
    :type conn: cloudbot.client.Client
    :type text: str
    :type event: cloudbot.event.CommandEvent
    """
    account, *perks = text.split()

    if not perks:
        event.notice_doc()
        return

    added = []

    for perk in perks:
        if check_perk(db, conn, account, perk):
            event.reply("{!r} already has the perk {!r}".format(account, perk))
        else:
            add_perk(db, conn, account, perk)

            added.append(perk)

    if len(added) == 1:
        return "Added {!r} perk to {!r}".format(added[0], account)

    return "Added perks: {!r} to {!r}".format(added, account)


@hook.command('listperks', permissions=['manage_patron'])
def cmd_list_perks(db, conn, text, event):
    """<account> - List the perks <account> currently has

    :type db: sqlalchemy.orm.Session
    :type conn: cloudbot.client.Client
    :type text: str
    :type event: cloudbot.event.CommandEvent
    """

    user = text
    perks = get_user_perks(db, conn, user)

    if not perks:
        return "{!r} has no perks".format(user)

    return "{!r} has perks: {!r}".format(user, perks)


@hook.command('delperk', permissions=['manage_patron'])
def cmd_del_perk(db, conn, text, event):
    """<account> <perk> [perk2] ... - Remove a patreon perk from a user's account

    :type db: sqlalchemy.orm.Session
    :type conn: cloudbot.client.Client
    :type text: str
    :type event: cloudbot.event.CommandEvent
    """
    account, *perks = text.split()

    if not perks:
        event.notice_doc()
        return

    removed = []

    for perk in perks:
        if check_perk(db, conn, account, perk):
            del_perk(db, conn, account, perk)
            removed.append(perk)
        else:
            event.reply("{!r} doesn't have the perk {!r}".format(account, perk))

    if len(removed) == 1:
        return "Removed {!r} perk from {!r}".format(removed[0], account)

    return "Removed perks: {!r} from {!r}".format(removed, account)


@hook.command('clearperks', permissions=['manage_patron'])
def cmd_clear_perks(db, conn, text):
    """<account> - Remove all perks from <account>

    :type db: sqlalchemy.orm.Session
    :type conn: cloudbot.client.Client
    :type text: str
    """
    user = text

    clear_perks(db, conn, user)

    return "Cleared all perks from {!r}".format(user)


def get_no_perk_msg(conn):
    try:
        return conn.config['plugins']['perkserv']['no_perk_msg']
    except KeyError:
        try:
            return conn.bot.config['plugins']['perkserv']['no_perk_msg']
        except KeyError:
            return "No message configured (missing perk)"


@hook.command('hidle', autohelp=False, clients=['irc'])
async def cmd_hideidle(db, nick, conn, event):
    """- Add the hideidle mode to yourself

    :type db: sqlalchemy.orm.Session
    :type nick: str
    :type conn: cloudbot.client.IrcClient
    :type event: cloudbot.event.CommandEvent
    """

    # Allow the whois processing to happen in the background
    await asyncio.sleep(2)
    account = conn.memory['users'].getuser(nick).account
    if not account:
        return "You must be logged in to an account"

    has_perk = await event.async_call(check_perk, db, conn, account, 'hideidle')
    if not has_perk:
        return get_no_perk_msg(conn).format(perk_name='hideidle')

    conn.cmd("SAMODE", nick, "+a")
    return "Done"

@hook.command('showidle', autohelp=False, clients=['irc'])
async def cmd_showidle(db, nick, conn, event):
	""" Remove the +a user mode from user. """
	# Allow the whois processing in background
	await asyncio.sleep(2)
	has_perk = await event.async_call(check_perk, db, conn, nick, 'showidle')
	if not has_perk:
		return get_no_perk_msg(conn).format(perk_name='showidle')

	conn.cmd("SAMODE", nick, "-a")
	return "Done"
