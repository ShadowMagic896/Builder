# async def nhentai(self, ctx: BuilderContext, code: int, ephemeral: bool = False):
#         """
#         Uses [nhentai.xxx](https://nhentai.xxx) to get all pages within a manga, and sends them to you.
#         """
#         file_chunk_size = 10
#         await ctx.interaction.response.defer(thinking=True)
#         baseurl = "nhentai.xxx/g/%s/" % code


#         embed = fmte(
#             ctx,
#             t = "Downloading Next Batch..."
#         )
#         m = await ctx.send(embed=embed)

#         files: List[discord.File] = []
#         page = -1
#         batch = 0
#         start_t = time.time()
#         batch_t = time.time()
#         file_t = time.time()
#         while True:
#             page += 1
#             soup = bs4.BeautifulSoup(await (await self.bot.session.get("https://%s%s" % (baseurl, page+1))).text(), "html.parser")
#             try:
#                 dataurl = soup.select("body > div#page-container > section#image-container > a > img")[0]["src"]
#             except IndexError:
#                 await ctx.send(files=files)
#                 files.clear()
#                 return
#             res = await self.bot.session.get(dataurl)
#             b: io.BytesIO = io.BytesIO(await res.read())
#             b.seek(0)
#             files.append(discord.File(b, filename="%s_%s.jpg" % (code, page+1)))
#             if len(files) % file_chunk_size == 0:
#                 # await m.remove_attachments(embed)
#                 embed = fmte(
#                     ctx,
#                     t = "Batch #%s Done" % (batch + 1),
#                     d = "File Time: `{}s`\nBatch Time: `{}s`\nTotal Time: `{}s`".format(
#                         round(t - file_t), round(t - batch_t), round(t - start_t)
#                     )
#                 )
#                 m = await ctx.send(embed=embed, files=files)
#                 files.clear()
#                 batch_t = time.time()
#                 batch += 1
#                 continue
#             else:
#                 t = time.time()
#                 embed = fmte(
#                     ctx,
#                     t = "Batch #%s File #%s Done" % (batch + 1, (page + 1) % file_chunk_size),
#                     d = "File Time: `{}s`\nBatch Time: `{}s`\nTotal Time: `{}s`".format(
#                         round(t - file_t), round(t - batch_t), round(t - start_t)
#                     )
#                 )
#                 await m.edit(embed=embed)
#                 file_t = time.time()
#                 continue


# class CodeModal(BaseModal):
#     def __init__(self, util: Utility, ctx: BuilderContext) -> None:
#         self.util = util
#         self.ctx: BuilderContext = ctx
#         super().__init__(title="Python Evaluation")

#     code = discord.ui.TextInput(
#         label="Please paste / type code here", style=discord.TextStyle.long
#     )

#     async def makeContainer(self, ctx: BuilderContext, inter: discord.Interaction):
#         """
#         Runs a contianer. Returns the result STDOUT, STDERR, and return code.
#         """
#         if ctx.author.id not in [
#             mem.id for mem in (await ctx.bot.application_info()).team.members
#         ]:
#             self.util.container_users.append(ctx.author.id)
#         value: str = self.code.value
#         basepath = f"{os.getcwd()}\\docker"

#         # Prepare Files for Building
#         _dir = len(os.listdir(f"{basepath}\\containers"))
#         dirpath = f"{basepath}\\containers\\{_dir}"
#         os.system(f"mkdir {dirpath}")

#         pypath = f"{dirpath}\\main.py"
#         with open(pypath, "w") as pyfile:
#             pyfile.write(value)

#         for f in os.listdir(f"{basepath}\\template"):
#             with open(f"{basepath}\\template\\{f}", "r") as template:
#                 with open(f"{dirpath}\\{f}", "w") as file:
#                     file.write(template.read())

#         options = {
#             "--rm": "",
#             "--memory": "6MB",
#             "--ulimit": "cpu=3",
#             "--read-only": "",
#             "-t": _dir,
#         }
#         opts = " ".join(
#             f"{x}{' ' if y != '' else y}{y}" for x, y in list(options.items())
#         )

#         # Build the Container
#         await (
#             await asyncio.create_subprocess_shell(
#                 f"cd {dirpath} && docker build -t {_dir} . ",
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.PIPE,
#             )
#         ).communicate()
#         print("Communicated")
#         embed = fmte(
#             ctx,
#             t=f"Container Created `[ID: {_dir}]`",
#             d="Compiling and running code...",
#         )
#         await inter.followup.send(embed=embed)
#         proc: Process = await asyncio.create_subprocess_shell(
#             f"cd {dirpath} && docker run {opts}",
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE,
#         )
#         stdout, stderr = await proc.communicate()
#         if stderr:
#             raise InternalError("This server's Docker daemon is not running right now.")

#         # Cleanup
#         await (
#             await asyncio.create_subprocess_shell(
#                 f"docker image prune -a --force",
#             )
#         ).communicate()
#         try:
#             self.util.container_users.remove(self.ctx.author.id)
#         except ValueError:
#             pass

#         return (_dir, stdout, (proc.returncode or 0))

#     async def on_submit(self, interaction: discord.Interaction) -> None:
#         estart = time.time()
#         await interaction.response.defer(thinking=True)
#         _dir, stdout, return_code = await self.makeContainer(self.ctx, interaction)

#         file: discord.File = ...
#         color: discord.Color = ...

#         color = discord.Color.teal() if return_code == 0 else discord.Color.red()

#         buffer = io.BytesIO()
#         buffer.write(stdout)
#         buffer.seek(0)

#         file = discord.File(buffer)
#         file.filename = f"result.{self.ctx.author.id}.py"
#         file.description = f"This is the result of a Python script written by Discord user {self.ctx.author.id}, and run in a Docker container."

#         embed = fmte(
#             self.ctx,
#             d=f"```py\n{self.code.value}\n\n# Finished in: {time.time() - estart} seconds\n# Written by: {self.ctx.author.id}```",
#             c=color,
#         )

#         await (await interaction.original_message()).edit(
#             content=None, embed=embed, attachments=(file,)
#         )
#         ddir = os.getcwd() + f"\\docker\\containers\\{_dir}"
#         os.system(f"rd /Q /S {ddir}")
