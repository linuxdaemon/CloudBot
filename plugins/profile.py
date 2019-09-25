import enum
import shlex
from typing import Optional

from sqlalchemy import Column, String, Enum, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from cloudbot import hook
from cloudbot.util import database


@enum.unique
class VoiceOption(enum.Enum):
    DISABLED = 0
    IS_REGISTERED = 1
    HAVE_PROFILE = 2
    IS_CAP = 3
    IS_LOWER = 4


class ProfileBase(database.base):
    __abstract__ = True

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ', '.join(
                '{}={!r}'.format(k.name, getattr(self, k.name))
                for k in self.__table__.columns
            )
        )


class Channel(ProfileBase):
    __tablename__ = 'profile_chans'

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)

    network = Column(String, index=True, nullable=False)
    channel = Column(String, index=True, nullable=False)

    autovoice_option = Column(Enum(VoiceOption), default=VoiceOption.DISABLED, nullable=False)
    require_account = Column(Boolean, default=False, nullable=False)
    need_profile_to_view = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint('network', 'channel'),
    )

    @classmethod
    def get(cls, session, network, channel) -> Optional['Channel']:
        return session.query(cls).filter_by(network=network.lower(), channel=channel.lower()).first()

    def get_field(self, name) -> Optional['ProfileField']:
        for field in self.fields:
            if field.name == name:
                return field

        return None

    def get_profile(self, nick) -> Optional['Profile']:
        for profile in self.profiles:
            if profile.user == nick:
                return profile

        return None

    def has_profile(self, nick) -> bool:
        return self.get_profile(nick) is not None

    @property
    def field_names(self):
        return [field.name for field in self.fields]


class ProfileField(ProfileBase):
    __tablename__ = 'profile_fields'

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)

    channel_id = Column(Integer, ForeignKey(Channel.id), index=True, nullable=False)
    channel = relationship(Channel, backref='fields')

    name = Column(String, nullable=False)
    description = Column(String)

    __table_args__ = (
        UniqueConstraint('name', 'channel_id'),
    )


class Profile(ProfileBase):
    __tablename__ = 'profiles'

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)

    channel_id = Column(Integer, ForeignKey(Channel.id), index=True, nullable=False)
    channel = relationship(Channel, backref='profiles')

    user = Column(String)

    def get_field(self, field: str) -> Optional['ProfileData']:
        for item in self.fields:
            if item.field.name == field:
                return item

        return None

    def set_field(self, session, field: 'ProfileField', data: str):
        old = self.get_field(field.name)
        if old:
            old.value = data
            return old

        row = ProfileData(field=field, value=data, profile=self)

        session.add(row)

        return row

    def unset_field(self, session, field: 'ProfileField'):
        old = self.get_field(field.name)
        if not old:
            return

        session.delete(old)


class ProfileData(ProfileBase):
    __tablename__ = 'profile_data'

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)

    field_id = Column(Integer, ForeignKey(ProfileField.id), index=True, nullable=False)
    field = relationship('ProfileField', foreign_keys=field_id)

    profile_id = Column(Integer, ForeignKey(Profile.id), index=True, nullable=False)
    profile = relationship('Profile', backref='fields')

    value = Column(String)

    __table_args__ = (
        UniqueConstraint('profile_id', 'field_id'),
    )


@hook.on_start()
def setup(db):
    db.query(ProfileData).delete()
    db.query(Profile).delete()
    db.query(ProfileField).delete()
    db.query(Channel).delete()
    db.commit()

    channel = Channel(network='snootest', channel='##ldtest')
    db.add(channel)

    channel.autovoice_option = VoiceOption.IS_REGISTERED

    channel.need_profile_to_view = True

    age_field = ProfileField(channel=channel, name="age")
    loc_field = ProfileField(channel=channel, name="location")

    db.add(age_field)
    db.add(loc_field)

    profile = Profile(channel=channel, user='linuxinthecloud')

    db.add(profile)

    profile.set_field(db, age_field, '21')
    profile.set_field(db, loc_field, 'USA')

    db.commit()


def get_field(channel: Channel, text):
    if not text:
        return None

    field = channel.get_field(text)
    return field


@hook.command('profile_set', autohelp=False)
def setup_profile(db, conn, chan, nick, text):
    channel = Channel.get(db, conn.name, chan)
    if not channel:
        return "Profiles not enabled in this channel"

    if not text:
        return "Fields: " + ', '.join(channel.field_names)

    split = text.split(None, 1)

    name = split.pop(0)

    if split:
        data = split.pop(0)
    else:
        data = None

    field = get_field(channel, name)

    if not field:
        return "Invalid field"

    profile = channel.get_profile(nick)

    if not profile:
        profile = Profile(user=nick, channel=channel)
        db.add(profile)
        db.commit()

    if data is None:
        profile.unset_field(db, field)
    else:
        profile.set_field(db, field, data)

    print(profile)
    db.commit()

    return "Done."


@hook.command('view_profile')
def view_profile(db, conn, chan, nick, text):
    """<nick> - View <nick>'s profile"""

    channel = Channel.get(db, conn.name, chan)
    if not channel:
        return "Profiles not enabled in this channel"

    viewer = nick
    target = text

    if channel.need_profile_to_view and not channel.has_profile(viewer):
        return "You need a profile to view someone else's"

    profile = channel.get_profile(target)
    if not profile:
        return "{} doesn't have a profile".format(target)

    data = {field.field.name: field.value for field in profile.fields}

    return "Profile: nick: {}".format(target) + " " + repr(data)


@hook.command('profile_add_field')
def add_field(db, conn, chan, text):
    """<field> [description] - Add a field to this channel's profile template called <field> with [description] as
    the description. The field name can be enclosed in " (double-quote) to use a name with spaces

    :type db: sqlalchemy.orm.Session
    :type conn: cloudbot.client.Client
    :type chan: str
    :type text: str
    """

    data = shlex.split(text)

    description = ' '.join(data[1:])

    config = Channel.get(db, conn.name, chan)

    db.add(ProfileField(channel=config, name=data[0], description=description))

    db.commit()

    return "Done."


@hook.command(autohelp=False)
def enable_profiles(db, conn, chan):
    config = Channel.get(db, conn.name, chan)

    if config:
        return "Profiles already enabled in this channel"

    db.add(Channel(network=conn.name.lower(), channel=chan.lower()))

    db.commit()

    return "Done."
