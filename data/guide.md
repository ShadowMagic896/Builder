# What This Is
This is a guide on how to create a basic bot with App Commands (Slash Commands) and Views (Buttons, Selects) using [Discord.py](https://github.com/Rapptz/discord.py)

# What This Is Not
This is **not** a comprehensive guide on everything possible with discord.py, nor will this hold your hand through concepts 
already mentioned in the following chapter.

### Some requirements:
**Basic-Intermediate knowledge of Python**

*Specifically OOP & asynchronous. 
Being familiar with wrapper logic is recommended, too.*

**The Ability to Read Documentation**

*The latest documentation for `Discord.py` is available [here](https://discordpy.readthedocs.io/en/latest/api.html)
If you want to get a deeper understanding of how something works or wish to know more information about something, please look for it in the documentation or use the great big internet to search for it. Please do not ask me or other people for help with questions that can be easilly answered by reading the documentation.*

**The Ability to Read Errors**

*Reading and understanding error tracebacks is **absoloutely** critical when learning anything, and dpy is no exception.
Learning how to know what is wrong, where it happened, and how to either ask for help or fix it yourself is a great way to save everyone's time.*

**A will to actually learn, and not just copy code from this guide.**

*I made this to help you learn, and just copying 
code without understanding makes this entire thing useless.*

## 1: Creating an Application

Go to [Discord Developers](https://discord.com/developers/applications) and create a new application.
![image](https://user-images.githubusercontent.com/86629697/168397798-ec584426-b9b9-471e-aeb9-a7dfe5064355.png)

Then, create the application's bot.
![image](https://user-images.githubusercontent.com/86629697/168398804-2007c81e-695e-4852-b85f-31e5eb7691a5.png)

You will need to generate a key. Click the `Reset Token` button to make a new one. **DO NOT SEND THIS TO ANYBODY, EVER.** GitHub can detect bot keys sent to their site and automatically voids them, but not all sites do this. You will get a DM from "Safety Jim" on Discord when this happens.

# 2: Intents, Scopes, & Invites
Under the `bot` tab, you may want to enable certain "privlaged intents." These are toggles that let the bot know certain information about a server such as:
- Message Content
- Guild Members
- Guild Members' Presences

Feel free to select the ones that you feel you would need. For this guide, none are used.

To invite the bot to a server, we must generate an `oauth` URL. Go to the `Oauth2 > URL Generator` tab, and select the `bot` and `applications.commands` scopes.

![image](https://user-images.githubusercontent.com/86629697/168400394-465e7cd5-d8c8-4cf4-824d-c6bd6779999d.png)


For this bot, we do not need any explicit permissions, so we can skip that part.

Copy the link at the bottom and paste it into any browser's URL bar.
From there, you can invite the bot to any server that you have the permission to do so in.

The URL should look like this:

`https://discord.com/api/oauth2/authorize?client_id=123456789123456789&permissions=0&scope=bot%20applications.commands`

The WebPage should look like this:

![image](https://user-images.githubusercontent.com/86629697/168400929-920f85ad-e5cb-408d-86c3-4b5c56657053.png)

With that all done, we can start coding!

# 3: Creating & Running the Bot
Create a new project / folder in your IDE of choice. I personally use [VSCode](https://code.visualstudio.com/), but others such as [SubLime](https://www.sublimetext.com/) and [IntelliJ](https://www.jetbrains.com/idea/) are more than great. However, **I do not recommend using [ReplIT](https://replit.com/) for this project.** While it is a neat service, there are many downsides that make it unsuitable for this.

Create a new folder and inside of it, make a python file. The name should probably be along the lines of `bot.py`.
Let's start by importing a few things.

```py
import discord
from discord.ext import commands
```

Next, let's create a bot.
For this guide, we will be subclassing our bot.
This means that instead of doing something like the following:

```py
# Not this!
bot = commands.Bot(...)
```

We will create a class that inherits from commands.Bot. Here's what that looks like.

```py
class MyCoolBot(commands.Bot):
    # Do stuff???
```

Next, add a `__init__`. This is where we will define our bot parameters and ultimately make our bot!

We will create our bot using `super()`, which gets the parent class of whever this is being run. In this case, `commands.Bot`, followed by `.__init__()`, which creates an instance of `commands.Bot`, a.k.a. our bot!

When making application commands, we also need to send our `application_id`. This can be gotten from our Developer Dashboard, in the General Information tab (under description and tags).

You may be wondering why I have such an odd prefix. This is because when you are not mentioned in a message, you do not see a message (without message_content intent).

The command prefix is just the bot's mention, so to call a command you would do `@TestBot 2000 hello` (which discord and bots see as `<@974806049376854046> hello`) and now it will see the message, recognize that the prefix is `<@974806049376854046> `, and then send the `hello` command.

Also, don't fret, this issue does not arise with slash commands. It only affects `hybrid_commands` and `commands`

Here's all of that written down.

```py
class MyCoolBot(commands.Bot):
    def __init__(self):
        command_prefix = "<@974806049376854046> "
        intents = discord.Intents.default()
		# Be sure to enable all intents here that you enabled in the dashboard
        application_id = 123456789123 # integer, not a string!

        super().__init__(
            command_prefix = command_prefix,
            intents = intents,
            application_id = application_id
        )
```

Here is also where you would create any botvars (variables stored publically in the bot for any cog or command to access) using `self.x = y`
Now we also need to make an on_ready function so we actually know when the bot is online. My preferred way is to use `setup_hook`, like so:

```py
    async def setup_hook(self):
        print(f"{self.name} is now online! [ID: {self.user.id}]")
        # Pro Tip: Don't do anything else here, otherwise stuff gets funky.
```

Because this class inherits from `Bot`, we can use methods and parameters from the `Bot` class (ie `setup_hook`)
This method is managed by discord.py, so we don't have to do anything else to actually call that.

Now we get to actually run the bot!
We need to create one more function to do that, though.

It will be an asynchronous fuction that does a few things
- Creates an instance of `MyCoolBot`
- Loads extensions
- Runs the bot

Here's what that looks like. (This should not be in the class)

```py
async def main(token: str):
    bot = MyCoolBot() # Create the bot instance
    # We will do more things here...
    await bot.start(token)
```

Now you may be wondering what `token` is. It's the key to your bot, so as long as nobody else knows about it, nobody else can run your bot in their own code. Remember when I was talking about that thing you shouldn't send to anyone? Grab that.

In order to use the `main` function, we need to add a new import: `asyncio`. This allows us to run our asynchronous functions without actually being in an asynchronous function.

The method in question is `asyncio.run(coroutine)`.

Use that method on `main`, passing your bot key as the `token` argument.

A quick note about keys:

If you plan to upload your code to a public repository, be sure to place that token in a different file, and have github ignore that file when you commit.

Here's what our code looks like now:

```py
import discord
from discord.ext import commands

import asyncio


class MyCoolBot(commands.Bot):
    def __init__(self):
        command_prefix = "!"
        intents = discord.Intents.default()
		# Be sure to enable all intents here that you enabled in the dashboard
        application_id = 123456789123456789 # integer, not a string!

        super().__init__(
            command_prefix = command_prefix,
            intents = intents,
            application_id = application_id
        )
        # this is similar to commands.Bot(...), because super() is just commands.Bot

    async def setup_hook(self):
        print(f"{self.user} is now online! [ID: {self.user.id}]")
        # Pro Tip: Don't do anything else here, otherwise stuff gets funky.

async def main(token: str):
    bot = MyCoolBot() # Create the bot instance
    # We will do more things here...
    await bot.start(token) # Run the bot

asyncio.run(main("YOUR BOT TOKEN HERE"))
```

And now, run that file!

In the server that you invited your bot to, you should see the bot go online. If it doesn't, double check your code & dashboard to make sure you didn't screw anything up.

*If you're 100% positive that you are correct, DM me @ Cookie?#9999 and I will correct this guide.*


# 4: Making an Extension

Now, you may notice that your bot cannot actually do anything. Let's fix that!

The most popular way to add commands is through `Cog`s. These simply groups of commands that are in a seperate class, and often in a different file.

You have have heard to terms `Cog` and `extension` being used interchangably, but this is incorrect.

`Cog` -> A seperate class that inherits `commadnds.Cog`

`extension` -> A seperate file, usually containing one or more `Cog`s

To make an extension, you must first ~~invent the universe~~ create a new python file. For this guide, it will be referred to as `extension.py`, but feel free to name it whatever you want.

In that file, add the same imports as before

```py
import discord
from discord.ext import commands
```

Then, make a class that inherits `commands.Cog`. This allows discord to recognize it as a cog to load commands from.

```py
class MyCoolCog(commands.Cog):
    # Do stuff???
```

When you create a `Cog`, it *must* have an `__init__` that takes an argument. This argument is your `bot`, so that you can use it on your commands, if you wish.

```py
    def __init__(self, bot: commands.Bot):
        self.bot = bot # Save it so self so that the functions (commands!) in this class can use it.
```

Now, let's add a `hybrid_command`

<span style="color:red">"WHAT?!?!?! I thought that you said we were making slash commands!!!!!?!??!?!?"</span>

Well, yes and no. `hybrid_commands` are the best of both worlds! They can be used either with text input (ie. `!help`), or as a slash command as we know and ~~sometimes~~ love them.

Also, they're just easier to work with because they inherit `commands.Command`, which is much more developed than `app_commands.command`, which means more features for you!

Sounds good? Good.

# 5: Creating Commands

To make a command, simply make any **async** method in your cog class, and add the deocrator `commands.hybrid_command()`. This decorator can take many options (check [docs](https://discordpy.readthedocs.io/en/latest/api.html)), but none are required.

All methods with this deocrator must take `self` (because it is in a class with `__init__`) as well as a `commands.Context` object. I am not joking when I say that `Context` is absoloutely amazing. If you want to do literally anything, there's a very high chance that you can do it with just `Context`.

The code that you put inside of the function is the code that will run when the user uses the command.

To manually respond / followup to an interaction, use `Context.interaction.response.send_message(...)`.

However, `Context` has a method that:
- If it is an interaction that has not been responded to, uses `ctx.interaction.response.send_message`
- If it is an interaction that has been responded to, uses `ctx.interaction.followup`
- If it is a text command, uses `ctx.message.channel.send`

This method is `await ctx.send`, and it is very nice.

Example:

```py
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello {ctx.author}!")
```

# 6: We Forgot Something

In order for our commands to load, we need to load the extenstions into our bot. Luckily, this is rather simple.

At the end of your extension file, create an `async` function called `setup`, that takes the param `bot`.

In the function, insert the following line:

```py
    await bot.add_cog(MyCoolCog(bot))
```

You can add that line for each cog you have in that extension file.

Here's what that the end function should look like:

```py
# Should probably be at the end of the file but I guess it can be anywhere
async def setup(bot):
    await bot.add_cog(MyCoolCog(bot))
```

What is does is simply add the `MyCoolCog` `Cog` to `bot`, and passing the `bot` into `MyCoolCog`'s `__init__` (to be placed in `self`, for the other commands to use)

This is what your extension file should look like now:

```py
import discord
from discord.ext import commands


class MyCoolCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(f"Hello {ctx.author}!")

async def setup(bot):
    await bot.add_cog(MyCoolCog(bot))
```

And now when your extension is loaded, `setup` gets run and all `Cog`s that you added will have their internal commands added to the bot!



# 7: We Forgot the Other Thing

So sorry, but we need one more step.

Back in your `bot.py` (Or whatever you named it), find your `main` async function.

After you define your bot, but before you actually start the bot, you need to load your extensions.

To do this is, once again, very simple.

Just use the method `bot.load_extension(extension)`. The bot uses import formatting to load extensions (not file paths)

So, if you had the following file tree

```
Folder
  | - bot.py
  | - extensions
          | - extension.py
```

You would use `bot.load_extension("extensions.extension")`. Notice that I do not include the `.py`, and I pass the entire extension file.

If your extension is in the same directory, however, you can just do `bot.load_extension("extension")`.

Your `main` should now look something like this:

```py
async def main(token: str):
    bot = MyCoolBot() # Create the bot instance
    
    await bot.load_extension("extension")

    await bot.start(token) # Run the bot
```

And now, if you didn't fudge it up, **you can now use the text part of this command**, ie `@TestBot 2000 hello`. (Watch the number of spaces between the command and the mention when sending the message, sometimes it can be odd)

![image](https://user-images.githubusercontent.com/86629697/168406861-07becb4f-bcc2-4f9c-b6da-a6c7c95f84eb.png)


# 8: Where Slash Command

To give our bot slash commands, we need to do one more thing. Syncing!

Syncing is essentially telling discord that we have new `application_commands` for them to register.

And, believe it or not, this is also easy to do.

All we need to do is create a command that calls `await bot.tree.sync()`. That's it. After calling that command and then waiting for a hot sec, the command should show up. This command should be in a cog, but can really be anywhere that gets loaded and has access to `bot`

Pro tip: `await bot.tree.sync` returns a list of `AppCommand`s of all commands synced. You can print the amount of the commands synced to make sure it's working!

Challenge: Make this command without taking a peek at how it's done! I want you to take what you just did and modify it to do something different.


<details> 
    <summary> Look to Check Answers! </summary>
    
    @commands.hybrid_command()
    async def sync(self, ctx: commands.Context):
        await self.bot.tree.sync()
    
    or, my recommended option:

    @commands.hybrid_command()
    async def sync(self, ctx: commands.Context):
        commands = await self.bot.tree.sync()
        await ctx.send(f"Syncing {len(commands)} commands...")


</details>

Now, call that command using text commands `@TestBot 2000 sync`, and then wait for Discord to add your slash commands.

If your bot sends `Syncing 2 commands...` (two commands being the `sync` command and the one we made a bit ago, `hello`), then it is working properly.

![image](https://user-images.githubusercontent.com/86629697/168407249-3603ab1b-5b8f-43ad-8287-9c27580fd0ee.png)

After waiting...

![image](https://user-images.githubusercontent.com/86629697/168407269-2f451a34-230a-414c-8047-d9aa3edc6c5c.png)

Feel free to use the commands! They should work just as well as text-input ones.

![image](https://user-images.githubusercontent.com/86629697/168407327-faf7abd1-ce92-4e3c-b323-88a3056a9578.png)
# 9: Parameters

Just like all functions in Python, commands can take parameters. In `app_command`s, ***all*** parameters except `ctx`, which is handled by `discord.py`, for all commands must have a type. There are several valid options to choose from:

**Builtins:**
- str: String of any size
- int: Whole number from -(2 ^ 52) -> 2 ^ 52
- float: Number from -(2 ^ 52) -> 2 ^ 52
- bool: True or False
- typing.Literal[opts, ...]: A forced list of options to choose from.
  
**Custom:**
- discord.Attachment: Any attachment such as image, text file, video, ...
- discord.Member: Any member (user in spefific guild)
- discord.User: Any user (any Discord user)
- discord.TextChannel / VoiceChannel / Thread
- discord.Role
- Optional[type]: Lets a parameter be optional (`x: y = None` is the same as `x: Optional[y]`)
- Converters: Custom converters. These are not covered in this guide, but are easy to make.

All parameters for a function go *after* `self` and `ctx`.

Examples:

```py
    @commands.hybrid_command()
    async def echo(self, ctx: commands.Context, message: str):
        await ctx.send(f"Echo! {message}")
```

```py
    @commands.hybrid_command()
    async def ban(self, ctx: commands.Context, member: discord.Member):
        # .ban() only works on members, not users
        await member.ban()
        await ctx.send(f"L, {member} was banned.")
```

`*` keywords do nothing on `app_command`s.

# 10: Adding A View

Neat! Just to recap, we:
- Create an instance of `commands.Bot`
- Load an extension with a `Cog` in it
- In that `Cog`, we made `hybrid_commands` that responded to an interaction.
- We also created a way to sync commands to Discord, using `bot.tree.sync`
- Looked really cool while doing it

Now, we get into the good stuff.

There are many ways to do buttons and selects. Here's a list of the best ones

## __Method One__

This method involves creating a class inheritng from `discord.ui.View`, then adding items using decorators.
Like most things that inherit, we need to call `super().__init__()` (remember the bot? Same idea.)

```py
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 90) # You can define timeout length in here. in seconds (How long it takes for the bot to stop caring about this.
```

You can use the decorators `discord.ui.button` and `discord.ui.select` to create buttons and select menus, respectively.

In the decorator for buttons, you have to define either the button label or emoji, and can define other optional params (like style, custom_id, etc.).

In the decorator for selects, you have to define at least one option, and can define other optional params (like placeholder, custom_id, etc.). Options should always be a `discord.SelectOption` object.

When using decorators, the function being wrapped must take `self`, `interaction: discord.Interaction`, and either `button: discord.ui.Button` or `select: discord.ui.Select`

The button's `callback` (what happens when the button is clicked) is automatically set to the function.

Here's some examples!

```py
    @discord.ui.button(label="Click Me!", emoji="\N{WHITE HEAVY CHECK MARK}")
    async def clickMe(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.send_message("You clicked me!!!! Thank you. Bye!")
    
    @discord.ui.select(placeholder="Please choose an option...", options=[discord.SelectOption(label = "Option One" value = "1"), discord.SelectOption(label="Option One" value="1")])
    async def chooseMe(self, inter: discord.Interaction, select: discord.ui.Select):
        # To get the option chosen, you have to use this. "values" can be more than one if the select's max_options was not also one.
        chosen = inter.data["values"][0]
        await inter.response.send_message(f"You chose option {chosen}!!!! Thank you. Bye!")
```

In order to put these items onto a message, we need to create an instance of this view and then add it as a parameter called `view` when sending the message.

Let's add these values on our `hello` commands, for convinence, because we already made it.

This is what it will look like:

```py
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        view = MyView()
        await ctx.send(f"Hello {ctx.author}!", view=view)
``` 

And there ya go! Whever the command is used, it sends the buttons and whenever a button is pressed, it runs the code in the item's `callback` (the code in the function)

The combined view looks like this:

```py
# Our view (should be in the same file as where were are using it. In this case, "extension.py")
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 90) # You can define timeout length in here, in seconds (How long it takes for the bot to stop caring about this)

    @discord.ui.button(label="Click Me!", emoji="\N{WHITE HEAVY CHECK MARK}", style=discord.ButtonStyle.primary)
    async def clickMe(self, inter: discord.Interaction, button: discord.ui.Button):
        await inter.response.send_message("You clicked me!!!! Thank you. Bye!")
    
    @discord.ui.select(placeholder="Please choose an option...", options=[
        discord.SelectOption(label="Option One", value="1"), 
        discord.SelectOption(label="Option Two", value="2")
    ])
    async def chooseMe(self, inter: discord.Interaction, select: discord.ui.Select):
        # To get the option chosen, you have to use this. "values" can be more than one if the select's max_options was not also one.
        # This returns the option's value, not the label.
        chosen = inter.data["values"][0]
        await inter.response.send_message(f"You chose option {chosen}!!!! Thank you. Bye!")

# In our command ... -> 
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        view = MyView()
        await ctx.send(f"Hello {ctx.author}!", view=view)
```

In general, this method is good if you need to use the same view multiple times, on separate messages.

## __Method Two__

Another way to add a view is to not only have the view inherit `discord.ui.View`, but also have the items inherit their respective types (discord.ui.Button, discord.ui.Select). 

Notice the difference in capitalization! `Button` and `Select` are the main classes, while `button` and `select` are used for decorators (like in Method One)

Here's how to do this!

```py
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 90) # You can define timeout length in here, in seconds (How long it takes for the bot to stop caring about this)
    # Nothing else here!

class clickMe(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click Me!", emoji="\N{WHITE HEAVY CHECK MARK}", style=discord.ButtonStyle.primary # Unlike method one, item parameters are defined here
        )
    
    # To create the callback for these kinds, we must create a new method called callback
    # They take the same params as the callbacks in Method One
    async def callback(self, inter: discord.Interaction, select: discord.ui.Select):
        await inter.response.send_message("You clicked me!!!! Thank you. Bye!")

class chooseMe(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Please choose an option...", options=[
            discord.SelectOption(label="Option One", value="1"), 
            discord.SelectOption(label="Option Two", value="2")
        ])
    
    async def callback(self, inter: discord.Interaction, select: discord.ui.Select):
        # Notice how the actual core of each callback is the same
        chosen = inter.data["values"][0]
        await inter.response.send_message(f"You chose option {chosen}!!!! Thank you. Bye!")
```

To put these on a message is a little bit more work.

You will need to call the method `discord.ui.View.add_item`, which adds a `button` or `select` to the view. In Method One, this is done automatically. Here, we have to do it manually after we make the view.

```py
    # Sticking with the hello example
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        view = MyView()

        # You can do this kind of chaining if you would like
        view.add_item(clickMe()).add_item(chooseMe())

        await ctx.send(f"Hello {ctx.author}!", view=view)
```

Bam, Method Two done. This does the exact same thing as Method One, just in a different fashion.

Here's the final code:

```py
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout = 90) # You can define timeout length in here, in seconds (How long it takes for the bot to stop caring about this)
    # Nothing else here!

class clickMe(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Click Me!", emoji="\N{WHITE HEAVY CHECK MARK}", style=discord.ButtonStyle.primary # Unlike method one, item parameters are defined here
        )
    
    # To create the callback for these kinds, we must create a new method called callback
    # They take the same params as the callbacks in Method One, minus the button. If you want to get the button object this is, you can just use self. (Because it is a button)
    async def callback(self, inter: discord.Interaction):
        await inter.response.send_message("You clicked me!!!! Thank you. Bye!")

class chooseMe(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Please choose an option...", options=[
            discord.SelectOption(label="Option One", value="1"), 
            discord.SelectOption(label="Option Two", value="2")
        ])
    
    async def callback(self, inter: discord.Interaction):
        chosen = inter.data["values"][0]
        await inter.response.send_message(f"You chose option {chosen}!!!! Thank you. Bye!")

# In our command ... -> 
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        view = MyView()

        view.add_item(clickMe()).add_item(chooseMe())

        await ctx.send(f"Hello {ctx.author}!", view=view)
```

This method is my personal favorite, and is great if you need to repeat an item in several different views, without recreating the entire thing. Very modular, kinda like make-your-own legos.

## __Method Three__

This method is probably the simplest of them all.

It involves just creating the view and items right then and there, and often involves lambdas.

Not much to this, to be honest...

```py
    @commands.hybrid_command()
    async def hello(self, ctx: commands.Context):
        view = discord.ui.View()

        button = discord.ui.Button(label="Click Me!", emoji="\N{WHITE HEAVY CHECK MARK}", style=discord.ButtonStyle.primary)

        # Notice how these callbacks don't take 'button' either, because you can access it through just the button object we just made
        async def buttonCallback(inter: discord.Interaction):
            await inter.response.send_message("You clicked me!!!! Thank you. Bye!")
            
        # Set the callback to that function. This is what discord.py calls when the button is pressed.
        button.callback = buttonCallback

        select = discord.ui.Select(
            placeholder="Please choose an option...", options=[
                discord.SelectOption(label="Option One", value="1"), 
                discord.SelectOption(label="Option Two", value="2")
            ])

        async def selectCallback(inter: discord.Interaction):
            chosen = inter.data["values"][0]
            await inter.response.send_message(f"You chose option {chosen}!!!! Thank you. Bye!")
        select.callback = selectCallback

        view.add_item(button).add_item(select)

        await ctx.send(f"Hello {ctx.author}!", view=view)
```

While this method is sometimes useful, it isn't great when you need to reuse the same items or view.

## __Result__

All of the methods return the same result and do the same thing:

![image](https://user-images.githubusercontent.com/86629697/168408761-c3862cff-0a5e-46d7-8823-00658000c9ac.png)

It just depends on how you are using these views, and what kind of programmer you are.

***
__This guide was made by Cookie?#9999, started and finished on 5-13-2022 (at 23:59, so I can say I made it in one day), as a gift to anyone who wants to make a Discord bot.__

*Because I know that someone will probably do this if I do not say this:*

__Do not distrubute any substantial amount of this piece of software without my express and written permission, and do not claim any non-zero amount of ownership over any non-zero amount of material in this software.__
***