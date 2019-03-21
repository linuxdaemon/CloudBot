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

        self.hooks = defaultdict(list)
        self.tables = []

    def load(self):
        setattr(self.code, LOADED_ATTR, True)
        for obj in self.code.__dict__.values():
            if callable(obj) and hasattr(obj, HOOK_ATTR):
                self.load_hook(obj)
            elif isinstance(obj, sqlalchemy.Table) and obj.metadata is database.metadata:
                self.load_table(obj)

    def load_hook(self, func):
        func_hooks = getattr(func, HOOK_ATTR)

        for hook_type, func_hook in func_hooks.items():
            self.hooks[hook_type].append(func_hook.make_full_hook(self))

        # delete the hook to free memory
        delattr(func, HOOK_ATTR)

    def load_table(self, tbl):
        self.tables.append(tbl)

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
