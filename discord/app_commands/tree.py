"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations
import inspect
import sys
import traceback

from typing import (
    Any,
    TYPE_CHECKING,
    Callable,
    Coroutine,
    Dict,
    Generator,
    Generic,
    List,
    Literal,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload,
)
from collections import Counter


from .namespace import Namespace, ResolveKey
from .models import AppCommand
from .commands import Command, ContextMenu, Group, _shorten
from .errors import (
    AppCommandError,
    CommandAlreadyRegistered,
    CommandNotFound,
    CommandSignatureMismatch,
    CommandLimitReached,
)
from ..errors import ClientException
from ..enums import AppCommandType, InteractionType
from ..utils import MISSING, _get_as_snowflake, _is_submodule

if TYPE_CHECKING:
    from ..types.interactions import ApplicationCommandInteractionData, ApplicationCommandInteractionDataOption
    from ..interactions import Interaction
    from ..client import Client
    from ..abc import Snowflake
    from .commands import ContextMenuCallback, CommandCallback, P, T

    ErrorFunc = Callable[
        [
            Interaction,
            Optional[Union[ContextMenu, Command[Any, ..., Any]]],
            AppCommandError,
        ],
        Coroutine[Any, Any, Any],
    ]

__all__ = ('CommandTree',)

ClientT = TypeVar('ClientT', bound='Client')

APP_ID_NOT_FOUND = (
    'Client does not have an application_id set. Either the function was called before on_ready '
    'was called or application_id was not passed to the Client constructor.'
)


def _retrieve_guild_ids(
    command: Any, guild: Optional[Snowflake] = MISSING, guilds: List[Snowflake] = MISSING
) -> Optional[Set[int]]:
    if guild is not MISSING and guilds is not MISSING:
        raise TypeError('cannot mix guild and guilds keyword arguments')

    # guilds=[] or guilds=[...]
    if guild is MISSING:
        # If no arguments are given then it should default to the ones
        # given to the guilds(...) decorator or None for global.
        if guilds is MISSING:
            return getattr(command, '_guild_ids', None)

        # guilds=[] is the same as global
        if len(guilds) == 0:
            return None

        return {g.id for g in guilds}

    # At this point it should be...
    # guild=None or guild=Object
    if guild is None:
        return None
    return {guild.id}


class CommandTree(Generic[ClientT]):
    """Represents a container that holds application command information.

    Parameters
    -----------
    client: :class:`~discord.Client`
        The client instance to get application command information from.
    """

    def __init__(self, client: ClientT):
        self.client: ClientT = client
        self._http = client.http
        self._state = client._connection

        if self._state._command_tree is not None:
            raise ClientException('This client already has an associated command tree.')

        self._state._command_tree = self
        self._guild_commands: Dict[int, Dict[str, Union[Command, Group]]] = {}
        self._global_commands: Dict[str, Union[Command, Group]] = {}
        # (name, guild_id, command_type): Command
        # The above two mappings can use this structure too but we need fast retrieval
        # by name and guild_id in the above case while here it isn't as important since
        # it's uncommon and N=5 anyway.
        self._context_menus: Dict[Tuple[str, Optional[int], int], ContextMenu] = {}

    async def fetch_commands(self, *, guild: Optional[Snowflake] = None) -> List[AppCommand]:
        """|coro|

        Fetches the application's current commands.

        If no guild is passed then global commands are fetched, otherwise
        the guild's commands are fetched instead.

        .. note::

            This includes context menu commands.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to fetch the commands from. If not passed then global commands
            are fetched instead.

        Raises
        -------
        HTTPException
            Fetching the commands failed.
        ClientException
            The application ID could not be found.

        Returns
        --------
        List[:class:`~discord.app_commands.AppCommand`]
            The application's commands.
        """
        if self.client.application_id is None:
            raise ClientException(APP_ID_NOT_FOUND)

        if guild is None:
            commands = await self._http.get_global_commands(self.client.application_id)
        else:
            commands = await self._http.get_guild_commands(self.client.application_id, guild.id)

        return [AppCommand(data=data, state=self._state) for data in commands]

    def copy_global_to(self, *, guild: Snowflake) -> None:
        """Copies all global commands to the specified guild.

        This method is mainly available for development purposes, as it allows you
        to copy your global commands over to a testing guild easily and prevent waiting
        an hour for the propagation.

        Note that this method will *override* pre-existing guild commands that would conflict.

        Parameters
        -----------
        guild: :class:`~discord.abc.Snowflake`
            The guild to copy the commands to.

        Raises
        --------
        CommandLimitReached
            The maximum number of commands was reached for that guild.
            This is currently 100 for slash commands and 5 for context menu commands.
        """

        try:
            mapping = self._guild_commands[guild.id].copy()
        except KeyError:
            mapping = {}

        mapping.update(self._global_commands)
        if len(mapping) > 100:
            raise CommandLimitReached(guild_id=guild.id, limit=100)

        ctx_menu: Dict[Tuple[str, Optional[int], int], ContextMenu] = {
            (name, guild.id, cmd_type): cmd
            for ((name, g, cmd_type), cmd) in self._context_menus.items()
            if g is None or g == guild.id
        }

        counter = Counter(cmd_type for _, _, cmd_type in ctx_menu)
        for cmd_type, count in counter.items():
            if count > 5:
                as_enum = AppCommandType(cmd_type)
                raise CommandLimitReached(guild_id=guild.id, limit=5, type=as_enum)

        self._context_menus.update(ctx_menu)
        self._guild_commands[guild.id] = mapping

    def add_command(
        self,
        command: Union[Command[Any, ..., Any], ContextMenu, Group],
        /,
        *,
        guild: Optional[Snowflake] = MISSING,
        guilds: List[Snowflake] = MISSING,
        override: bool = False,
    ) -> None:
        """Adds an application command to the tree.

        This only adds the command locally -- in order to sync the commands
        and enable them in the client, :meth:`sync` must be called.

        The root parent of the command is added regardless of the type passed.

        Parameters
        -----------
        command: Union[:class:`Command`, :class:`Group`]
            The application command or group to add.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to add the command to. If not given or ``None`` then it
            becomes a global command instead.
        guilds: List[:class:`~discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed
            with the ``guild`` parameter. If no guilds are given at all
            then it becomes a global command instead.
        override: :class:`bool`
            Whether to override a command with the same name. If ``False``
            an exception is raised. Default is ``False``.

        Raises
        --------
        ~discord.app_commands.CommandAlreadyRegistered
            The command was already registered and no override was specified.
        TypeError
            The application command passed is not a valid application command.
            Or, ``guild`` and ``guilds`` were both given.
        CommandLimitReached
            The maximum number of commands was reached globally or for that guild.
            This is currently 100 for slash commands and 5 for context menu commands.
        """

        guild_ids = _retrieve_guild_ids(command, guild, guilds)
        if isinstance(command, ContextMenu):
            type = command.type.value
            name = command.name

            def _context_menu_add_helper(
                guild_id: Optional[int],
                data: Dict[Tuple[str, Optional[int], int], ContextMenu],
                name: str = name,
                type: int = type,
            ) -> None:
                key = (name, guild_id, type)
                found = key in self._context_menus
                if found and not override:
                    raise CommandAlreadyRegistered(name, guild_id)

                total = sum(1 for _, g, t in self._context_menus if g == guild_id and t == type)
                if total + found > 5:
                    raise CommandLimitReached(guild_id=guild_id, limit=5, type=AppCommandType(type))
                data[key] = command

            if guild_ids is None:
                _context_menu_add_helper(None, self._context_menus)
            else:
                current: Dict[Tuple[str, Optional[int], int], ContextMenu] = {}
                for guild_id in guild_ids:
                    _context_menu_add_helper(guild_id, current)

                # Update at the end in order to make sure the update is atomic.
                # An error during addition could end up making the context menu mapping
                # have a partial state
                self._context_menus.update(current)
            return
        elif not isinstance(command, (Command, Group)):
            raise TypeError(f'Expected a application command, received {command.__class__!r} instead')

        # todo: validate application command groups having children (required)

        root = command.root_parent or command
        name = root.name
        if guild_ids is not None:
            # Validate that the command can be added first, before actually
            # adding it into the mapping. This ensures atomicity.
            for guild_id in guild_ids:
                commands = self._guild_commands.get(guild_id, {})
                found = name in commands
                if found and not override:
                    raise CommandAlreadyRegistered(name, guild_id)
                if len(commands) + found > 100:
                    raise CommandLimitReached(guild_id=guild_id, limit=100)

            # Actually add the command now that it has been verified to be okay.
            for guild_id in guild_ids:
                commands = self._guild_commands.setdefault(guild_id, {})
                commands[name] = root
        else:
            found = name in self._global_commands
            if found and not override:
                raise CommandAlreadyRegistered(name, None)
            if len(self._global_commands) + found > 100:
                raise CommandLimitReached(guild_id=None, limit=100)
            self._global_commands[name] = root

    @overload
    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user],
    ) -> Optional[ContextMenu]:
        ...

    @overload
    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> Optional[Union[Command[Any, ..., Any], Group]]:
        ...

    @overload
    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: AppCommandType,
    ) -> Optional[Union[Command[Any, ..., Any], ContextMenu, Group]]:
        ...

    def remove_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Optional[Union[Command[Any, ..., Any], ContextMenu, Group]]:
        """Removes an application command from the tree.

        This only removes the command locally -- in order to sync the commands
        and remove them in the client, :meth:`sync` must be called.

        Parameters
        -----------
        command: :class:`str`
            The name of the root command to remove.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to remove the command from. If not given or ``None`` then it
            removes a global command instead.
        type: :class:`~discord.AppCommandType`
            The type of command to remove. Defaults to :attr:`~discord.AppCommandType.chat_input`,
            i.e. slash commands.

        Returns
        ---------
        Optional[Union[:class:`Command`, :class:`ContextMenu`, :class:`Group`]]
            The application command that got removed.
            If nothing was removed then ``None`` is returned instead.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                return self._global_commands.pop(command, None)
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return None
                else:
                    return commands.pop(command, None)
        elif type in (AppCommandType.user, AppCommandType.message):
            guild_id = None if guild is None else guild.id
            key = (command, guild_id, type.value)
            return self._context_menus.pop(key, None)

    @overload
    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user],
    ) -> Optional[ContextMenu]:
        ...

    @overload
    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> Optional[Union[Command[Any, ..., Any], Group]]:
        ...

    @overload
    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = ...,
        type: AppCommandType,
    ) -> Optional[Union[Command[Any, ..., Any], ContextMenu, Group]]:
        ...

    def get_command(
        self,
        command: str,
        /,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Optional[Union[Command[Any, ..., Any], ContextMenu, Group]]:
        """Gets a application command from the tree.

        Parameters
        -----------
        command: :class:`str`
            The name of the root command to get.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to get the command from. If not given or ``None`` then it
            gets a global command instead.
        type: :class:`~discord.AppCommandType`
            The type of command to get. Defaults to :attr:`~discord.AppCommandType.chat_input`,
            i.e. slash commands.

        Returns
        ---------
        Optional[Union[:class:`Command`, :class:`ContextMenu`, :class:`Group`]]
            The application command that was found.
            If nothing was found then ``None`` is returned instead.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                return self._global_commands.get(command)
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return None
                else:
                    return commands.get(command)
        elif type in (AppCommandType.user, AppCommandType.message):
            guild_id = None if guild is None else guild.id
            key = (command, guild_id, type.value)
            return self._context_menus.get(key)

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user],
    ) -> List[ContextMenu]:
        ...

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input],
    ) -> List[Union[Command[Any, ..., Any], Group]]:
        ...

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: AppCommandType,
    ) -> Union[List[Union[Command[Any, ..., Any], Group]], List[ContextMenu]]:
        ...

    @overload
    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Optional[AppCommandType] = ...,
    ) -> List[Union[Command[Any, ..., Any], Group, ContextMenu]]:
        ...

    def get_commands(
        self,
        *,
        guild: Optional[Snowflake] = None,
        type: Optional[AppCommandType] = None,
    ) -> Union[
        List[ContextMenu],
        List[Union[Command[Any, ..., Any], Group]],
        List[Union[Command[Any, ..., Any], Group, ContextMenu]],
    ]:
        """Gets all application commands from the tree.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to get the commands from, not including global commands.
            If not given or ``None`` then only global commands are returned.
        type: Optional[:class:`~discord.AppCommandType`]
            The type of commands to get. When not given or ``None``, then all
            command types are returned.

        Returns
        ---------
        List[Union[:class:`ContextMenu`, :class:`Command`, :class:`Group`]]
            The application commands from the tree.
        """
        if type is None:
            return self._get_all_commands(guild=guild)

        if type is AppCommandType.chat_input:
            if guild is None:
                return list(self._global_commands.values())
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return []
                else:
                    return list(commands.values())
        else:
            guild_id = None if guild is None else guild.id
            value = type.value
            return [command for ((_, g, t), command) in self._context_menus.items() if g == guild_id and t == value]

    @overload
    def walk_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.message, AppCommandType.user],
    ) -> Generator[ContextMenu, None, None]:
        ...

    @overload
    def walk_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: Literal[AppCommandType.chat_input] = ...,
    ) -> Generator[Union[Command[Any, ..., Any], Group], None, None]:
        ...

    @overload
    def walk_commands(
        self,
        *,
        guild: Optional[Snowflake] = ...,
        type: AppCommandType,
    ) -> Union[Generator[Union[Command[Any, ..., Any], Group], None, None], Generator[ContextMenu, None, None]]:
        ...

    def walk_commands(
        self,
        *,
        guild: Optional[Snowflake] = None,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Union[Generator[Union[Command[Any, ..., Any], Group], None, None], Generator[ContextMenu, None, None]]:
        """An iterator that recursively walks through all application commands and child commands from the tree.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to iterate the commands from, not including global commands.
            If not given or ``None`` then only global commands are iterated.
        type: :class:`~discord.AppCommandType`
            The type of commands to iterate over. Defaults to :attr:`~discord.AppCommandType.chat_input`,
            i.e. slash commands.

        Yields
        ---------
        Union[:class:`ContextMenu`, :class:`Command`, :class:`Group`]
            The application commands from the tree.
        """

        if type is AppCommandType.chat_input:
            if guild is None:
                for cmd in self._global_commands.values():
                    yield cmd
                    if isinstance(cmd, Group):
                        yield from cmd.walk_commands()
            else:
                try:
                    commands = self._guild_commands[guild.id]
                except KeyError:
                    return
                else:
                    for cmd in commands.values():
                        yield cmd
                        if isinstance(cmd, Group):
                            yield from cmd.walk_commands()
        else:
            guild_id = None if guild is None else guild.id
            value = type.value
            for ((_, g, t), command) in self._context_menus.items():
                if g == guild_id and t == value:
                    yield command

    def _get_all_commands(
        self, *, guild: Optional[Snowflake] = None
    ) -> List[Union[Command[Any, ..., Any], Group, ContextMenu]]:
        if guild is None:
            base: List[Union[Command[Any, ..., Any], Group, ContextMenu]] = list(self._global_commands.values())
            base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g is None)
            return base
        else:
            try:
                commands = self._guild_commands[guild.id]
            except KeyError:
                guild_id = guild.id
                return [cmd for ((_, g, _), cmd) in self._context_menus.items() if g == guild_id]
            else:
                base: List[Union[Command[Any, ..., Any], Group, ContextMenu]] = list(commands.values())
                guild_id = guild.id
                base.extend(cmd for ((_, g, _), cmd) in self._context_menus.items() if g == guild_id)
                return base

    def _remove_with_module(self, name: str) -> None:
        remove: List[Any] = []
        for key, cmd in self._context_menus.items():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                remove.append(key)

        for key in remove:
            del self._context_menus[key]

        remove = []
        for key, cmd in self._global_commands.items():
            if cmd.module is not None and _is_submodule(name, cmd.module):
                remove.append(key)

        for key in remove:
            del self._global_commands[key]

        for mapping in self._guild_commands.values():
            remove = []
            for key, cmd in mapping.items():
                if cmd.module is not None and _is_submodule(name, cmd.module):
                    remove.append(key)

            for key in remove:
                del mapping[key]

    async def on_error(
        self,
        interaction: Interaction,
        command: Optional[Union[ContextMenu, Command[Any, ..., Any]]],
        error: AppCommandError,
    ) -> None:
        """|coro|

        A callback that is called when any command raises an :exc:`AppCommandError`.

        The default implementation prints the traceback to stderr if the command does
        not have any error handlers attached to it.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction that is being handled.
        command: Optional[Union[:class:`~discord.app_commands.Command`, :class:`~discord.app_commands.ContextMenu`]]
            The command that failed, if any.
        error: :exc:`AppCommandError`
            The exception that was raised.
        """

        if command is not None:
            if command._has_any_error_handlers():
                return

            print(f'Ignoring exception in command {command.name!r}:', file=sys.stderr)
        else:
            print(f'Ignoring exception in command tree:', file=sys.stderr)

        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def error(self, coro: ErrorFunc) -> ErrorFunc:
        """A decorator that registers a coroutine as a local error handler.

        This must match the signature of the :meth:`on_error` callback.

        The error passed will be derived from :exc:`AppCommandError`.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine or does
            not match the signature.
        """

        if not inspect.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        params = inspect.signature(coro).parameters
        if len(params) != 3:
            raise TypeError('error handler must have 3 parameters')

        # Type checker doesn't like overriding methods like this
        self.on_error = coro  # type: ignore
        return coro

    def command(
        self,
        *,
        name: str = MISSING,
        description: str = MISSING,
        guild: Optional[Snowflake] = MISSING,
        guilds: List[Snowflake] = MISSING,
    ) -> Callable[[CommandCallback[Group, P, T]], Command[Group, P, T]]:
        """Creates an application command directly under this tree.

        Parameters
        ------------
        name: :class:`str`
            The name of the application command. If not given, it defaults to a lower-case
            version of the callback name.
        description: :class:`str`
            The description of the application command. This shows up in the UI to describe
            the application command. If not given, it defaults to the first line of the docstring
            of the callback shortened to 100 characters.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to add the command to. If not given or ``None`` then it
            becomes a global command instead.
        guilds: List[:class:`~discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed
            with the ``guild`` parameter. If no guilds are given at all
            then it becomes a global command instead.
        """

        def decorator(func: CommandCallback[Group, P, T]) -> Command[Group, P, T]:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('command function must be a coroutine function')

            if description is MISSING:
                if func.__doc__ is None:
                    desc = '…'
                else:
                    desc = _shorten(func.__doc__)
            else:
                desc = description

            command = Command(
                name=name if name is not MISSING else func.__name__,
                description=desc,
                callback=func,
                parent=None,
            )
            self.add_command(command, guild=guild, guilds=guilds)
            return command

        return decorator

    def context_menu(
        self,
        *,
        name: str = MISSING,
        guild: Optional[Snowflake] = MISSING,
        guilds: List[Snowflake] = MISSING,
    ) -> Callable[[ContextMenuCallback], ContextMenu]:
        """Creates a application command context menu from a regular function directly under this tree.

        This function must have a signature of :class:`~discord.Interaction` as its first parameter
        and taking either a :class:`~discord.Member`, :class:`~discord.User`, or :class:`~discord.Message`,
        or a :obj:`typing.Union` of ``Member`` and ``User`` as its second parameter.

        Examples
        ---------

        .. code-block:: python3

            @app_commands.context_menu()
            async def react(interaction: discord.Interaction, message: discord.Message):
                await interaction.response.send_message('Very cool message!', ephemeral=True)

            @app_commands.context_menu()
            async def ban(interaction: discord.Interaction, user: discord.Member):
                await interaction.response.send_message(f'Should I actually ban {user}...', ephemeral=True)

        Parameters
        ------------
        name: :class:`str`
            The name of the context menu command. If not given, it defaults to a title-case
            version of the callback name. Note that unlike regular slash commands this can
            have spaces and upper case characters in the name.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to add the command to. If not given or ``None`` then it
            becomes a global command instead.
        guilds: List[:class:`~discord.abc.Snowflake`]
            The list of guilds to add the command to. This cannot be mixed
            with the ``guild`` parameter. If no guilds are given at all
            then it becomes a global command instead.
        """

        def decorator(func: ContextMenuCallback) -> ContextMenu:
            if not inspect.iscoroutinefunction(func):
                raise TypeError('context menu function must be a coroutine function')

            actual_name = func.__name__.title() if name is MISSING else name
            context_menu = ContextMenu(name=actual_name, callback=func)
            self.add_command(context_menu, guild=guild, guilds=guilds)
            return context_menu

        return decorator

    async def sync(self, *, guild: Optional[Snowflake] = None) -> List[AppCommand]:
        """|coro|

        Syncs the application commands to Discord.

        This must be called for the application commands to show up.

        Global commands take up to 1-hour to propagate but guild
        commands propagate instantly.

        Parameters
        -----------
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to sync the commands to. If ``None`` then it
            syncs all global commands instead.

        Raises
        -------
        HTTPException
            Syncing the commands failed.
        Forbidden
            The client does not have the ``applications.commands`` scope in the guild.
        ClientException
            The client does not have an application ID.

        Returns
        --------
        List[:class:`AppCommand`]
            The application's commands that got synced.
        """

        if self.client.application_id is None:
            raise ClientException(APP_ID_NOT_FOUND)

        commands = self._get_all_commands(guild=guild)
        payload = [command.to_dict() for command in commands]
        if guild is None:
            data = await self._http.bulk_upsert_global_commands(self.client.application_id, payload=payload)
        else:
            data = await self._http.bulk_upsert_guild_commands(self.client.application_id, guild.id, payload=payload)

        return [AppCommand(data=d, state=self._state) for d in data]

    def _from_interaction(self, interaction: Interaction):
        async def wrapper():
            try:
                await self.call(interaction)
            except AppCommandError as e:
                await self.on_error(interaction, None, e)

        self.client.loop.create_task(wrapper(), name='CommandTree-invoker')

    def _get_context_menu(self, data: ApplicationCommandInteractionData) -> Optional[ContextMenu]:
        name = data['name']
        guild_id = _get_as_snowflake(data, 'guild_id')
        return self._context_menus.get((name, guild_id, data.get('type', 1)))

    def _get_app_command_options(
        self, data: ApplicationCommandInteractionData
    ) -> Tuple[Command[Any, ..., Any], List[ApplicationCommandInteractionDataOption]]:
        parents: List[str] = []
        name = data['name']

        command_guild_id = _get_as_snowflake(data, 'guild_id')
        if command_guild_id:
            try:
                guild_commands = self._guild_commands[command_guild_id]
            except KeyError:
                command = None
            else:
                command = guild_commands.get(name)
        else:
            command = self._global_commands.get(name)

        # If it's not found at this point then it's not gonna be found at any point
        if command is None:
            raise CommandNotFound(name, parents)

        # This could be done recursively but it'd be a bother due to the state needed
        # to be tracked above like the parents, the actual command type, and the
        # resulting options we care about
        searching = True
        options: List[ApplicationCommandInteractionDataOption] = data.get('options', [])
        while searching:
            for option in options:
                # Find subcommands
                if option.get('type', 0) in (1, 2):
                    parents.append(name)
                    name = option['name']
                    command = command._get_internal_command(name)
                    if command is None:
                        raise CommandNotFound(name, parents)
                    options = option.get('options', [])
                    break
                else:
                    searching = False
                    break
            else:
                break

        if isinstance(command, Group):
            # Right now, groups can't be invoked. This is a Discord limitation in how they
            # do slash commands. So if we're here and we have a Group rather than a Command instance
            # then something in the code is out of date from the data that Discord has.
            raise CommandSignatureMismatch(command)

        return (command, options)

    async def _call_context_menu(self, interaction: Interaction, data: ApplicationCommandInteractionData, type: int) -> None:
        name = data['name']
        guild_id = _get_as_snowflake(data, 'guild_id')
        ctx_menu = self._context_menus.get((name, guild_id, type))
        # Pre-fill the cached slot to prevent re-computation
        interaction._cs_command = ctx_menu

        if ctx_menu is None:
            raise CommandNotFound(name, [], AppCommandType(type))

        resolved = Namespace._get_resolved_items(interaction, data.get('resolved', {}))

        target_id = data.get('target_id')
        # Right now, the only types are message and user
        # Therefore, there's no conflict with snowflakes

        # This will always work at runtime
        key = ResolveKey.any_with(target_id)  # type: ignore
        value = resolved.get(key)
        if ctx_menu.type.value != type:
            raise CommandSignatureMismatch(ctx_menu)

        if value is None:
            raise AppCommandError('This should not happen if Discord sent well-formed data.')

        # I assume I don't have to type check here.
        try:
            await ctx_menu._invoke(interaction, value)
        except AppCommandError as e:
            if ctx_menu.on_error is not None:
                await ctx_menu.on_error(interaction, e)
            await self.on_error(interaction, ctx_menu, e)

    async def interaction_check(self, interaction: Interaction, /) -> bool:
        """|coro|

        A global check to determine if an :class:`~discord.Interaction` should
        be processed by the tree.

        The default implementation returns True (all interactions are processed),
        but can be overridden if custom behaviour is desired.
        """
        return True

    async def call(self, interaction: Interaction) -> None:
        """|coro|

        Given an :class:`~discord.Interaction`, calls the matching
        application command that's being invoked.

        This is usually called automatically by the library.

        Parameters
        -----------
        interaction: :class:`~discord.Interaction`
            The interaction to dispatch from.

        Raises
        --------
        CommandNotFound
            The application command referred to could not be found.
        CommandSignatureMismatch
            The interaction data referred to a parameter that was not found in the
            application command definition.
        AppCommandError
            An error occurred while calling the command.
        """
        if not await self.interaction_check(interaction):
            return

        data: ApplicationCommandInteractionData = interaction.data  # type: ignore
        type = data.get('type', 1)
        if type != 1:
            # Context menu command...
            await self._call_context_menu(interaction, data, type)
            return

        command, options = self._get_app_command_options(data)

        # Pre-fill the cached slot to prevent re-computation
        interaction._cs_command = command

        # At this point options refers to the arguments of the command
        # and command refers to the class type we care about
        namespace = Namespace(interaction, data.get('resolved', {}), options)

        # Same pre-fill as above
        interaction._cs_namespace = namespace

        # Auto complete handles the namespace differently... so at this point this is where we decide where that is.
        if interaction.type is InteractionType.autocomplete:
            focused = next((opt['name'] for opt in options if opt.get('focused')), None)
            if focused is None:
                raise AppCommandError('This should not happen, but there is no focused element. This is a Discord bug.')
            await command._invoke_autocomplete(interaction, focused, namespace)
            return

        try:
            await command._invoke_with_namespace(interaction, namespace)
        except AppCommandError as e:
            await command._invoke_error_handler(interaction, e)
            await self.on_error(interaction, command, e)