class BotFuncs:
    def get_cust_mapping(bot, exclude_none = True):
        mapping = {}
        for c in bot.commands:
            if c.cog in mapping.keys():
                mapping[c.cog].append(c)
            elif c.cog != None or not exclude_none:
                mapping[c.cog] = [c,]
        return mapping
    