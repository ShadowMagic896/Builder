# async def nhentai(self, ctx: commands.Context, code: int, ephemeral: bool = False):
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