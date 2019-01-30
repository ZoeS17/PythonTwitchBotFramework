import os
import traceback
from inspect import isclass

from typing import Dict
from .util import temp_syspath, get_py_files, get_file_name
from .channel import Channel
from .command import Command
from .config import cfg
from .enums import Event
from .message import Message
from importlib import import_module

__all__ = ('ensure_mods_folder_exists', 'Mod', 'register_mod', 'unregister_mod', 'trigger_mod_event', 'mods',
           'load_mods_from_directory')


# noinspection PyMethodMayBeStatic
class Mod:
    name = 'DEFAULT'

    @property
    def can_register(self):
        """
        can this mod be registered?
        :return: a bool indicating if the mod can be enabled
        """
        return True

    @property
    def can_unregister(self):
        """
        can this mod be unregistered?
        :return: a bool indicating if the mod can be unregistered
        """
        return True

    def register(self):
        """
        triggered when the mod is registered
        """

    def unregister(self):
        """
        triggered when the mod is unregistered
        """

    # region events
    async def on_connected(self):
        """
        triggered when the bot connects to all the channels specified in the config file
        """

    async def on_privmsg_sent(self, msg: str, channel: str, sender: str):
        """
        triggered when the bot sends a privmsg
        """

    async def on_privmsg_received(self, msg: Message):
        """
        triggered when a privmsg is received, is not triggered if the msg is a command
        """

    async def on_whisper_sent(self, msg: str, receiver: str, sender: str):
        """
        triggered when the bot sends a whisper to someone
        """

    async def on_whisper_received(self, msg: Message):
        """
        triggered when a user sends the bot a whisper
        """

    async def on_before_command_execute(self, msg: Message, cmd: Command) -> bool:
        """
        triggered before a command is executed
        :return bool, if return value is False, then the command will not be executed
        """
        return True

    async def on_after_command_execute(self, msg: Message, cmd: Command):
        """
        triggered after a command has executed
        """

    async def on_bits_donated(self, msg: Message, bits: int):
        """
        triggered when a bit donation is posted in chat
        """

    async def on_channel_joined(self, channel: Channel):
        """
        triggered when the bot joins a channel
        """
    # endregion


mods: Dict[str, Mod] = {}


def register_mod(mod: Mod) -> bool:
    """
    registers a mod globally
    :param mod: the mod to register
    :return: if registration was successful
    """
    if mod.name in mods or not mod.can_register:
        return False

    mods[mod.name] = mod
    mod.register()
    return True


def unregister_mod(mod: Mod) -> bool:
    """
    unregisters a mod globally
    :param mod:
    :return:
    """
    if not mod.can_unregister:
        return False

    if mod.name in mods:
        del mods[mod.name]
        mod.unregister()
        return True

    return False


async def trigger_mod_event(event: Event, *args):
    async def _missing_function(*ignored):
        pass

    for mod in mods.values():
        try:
            await getattr(mod, event.value, _missing_function)(*args)
        except Exception as e:
            print(f'\nerror has occurred while triggering a event on a mod, details:\n'
                  f'mod: {mod.name}\n'
                  f'event: {event}\n'
                  f'error: {type(e)}\n'
                  f'reason: {e}\n'
                  f'stack trace:\n')
            traceback.print_exc()


def ensure_mods_folder_exists():
    if not os.path.exists(cfg.mods_folder):
        os.mkdir(cfg.mods_folder)


def load_mods_from_directory(fullpath):
    print('loading mods from:', fullpath)

    with temp_syspath(fullpath):
        for file in get_py_files(fullpath):
            # we need to import the module to get its attributes
            module = import_module(get_file_name(file))
            for obj in module.__dict__.values():
                # verify the obj is a class, is a subclass of Mod, and is not Mod class itself
                if not isclass(obj) or not issubclass(obj, Mod) or obj is Mod:
                    continue
                # create a instance of the mod subclass, then register it
                register_mod(obj())