import logging
from collections import defaultdict

import sqlalchemy

from .util import database

LOADED_ATTR = '_cloudbot_loaded'
HOOK_ATTR = '_cloudbot_hook'

logger = logging.getLogger("cloudbot")


class Plugin:
    """
    Each Plugin represents a plugin file, and contains loaded hooks.

    :type file_path: str
    :type file_name: str
    :type title: str
    :type hooks: dict
    :type tables: list[sqlalchemy.Table]
    """

    def __init__(self, filepath, filename, title, code):
        """
        :type filepath: str
        :type filename: str
        :type code: object
        """
        self.tasks = []
        self.file_path = filepath
        self.file_name = filename
        self.title = title
        # Keep a reference to this in case another plugin needs to access it
        self.code = code

        self.hooks = self.load_hooks()
        # we need to find tables for each plugin so that they can be unloaded from the global metadata when the
        # plugin is reloaded
        self.tables = self.find_tables()

    def load_hooks(self):
        """
        :rtype: dict
        """
        # set the loaded flag
        setattr(self.code, LOADED_ATTR, True)
        hooks = defaultdict(list)
        for func in self.code.__dict__.values():
            if hasattr(func, HOOK_ATTR):
                # if it has cloudbot hook
                func_hooks = getattr(func, HOOK_ATTR)

                for hook_type, func_hook in func_hooks.items():
                    hooks[hook_type].append(func_hook.make_full_hook(self))

                # delete the hook to free memory
                delattr(func, HOOK_ATTR)

        return hooks

    def find_tables(self):
        """
        :rtype: list[sqlalchemy.Table]
        """
        tables = []
        for obj in self.code.__dict__.values():
            if isinstance(obj, sqlalchemy.Table) and obj.metadata == database.metadata:
                # if it's a Table, and it's using our metadata, append it to the list
                tables.append(obj)

        return tables

    async def create_tables(self, bot):
        """
        Creates all sqlalchemy Tables that are registered in this plugin

        :type bot: cloudbot.bot.CloudBot
        """
        if self.tables:
            # if there are any tables

            logger.info("Registering tables for %s", self.title)

            for table in self.tables:
                if not (await bot.loop.run_in_executor(None, table.exists, bot.db_engine)):
                    await bot.loop.run_in_executor(None, table.create, bot.db_engine)

    def unregister_tables(self, bot):
        """
        Unregisters all sqlalchemy Tables registered to the global metadata by this plugin
        :type bot: cloudbot.bot.CloudBot
        """
        if self.tables:
            # if there are any tables
            logger.info("Unregistering tables for %s", self.title)

            for table in self.tables:
                bot.db_metadata.remove(table)
