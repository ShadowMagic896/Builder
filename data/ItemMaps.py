class ItemMaps:
    def allItems():
        return {
            # Organic Nature
            "wood": ("aa", 5),
            "thatch": ("ab", 3),
            "palm_leaf": ("ac", 3),
            "pine_needle": ("ad", 1),

            # Inorganic Nature
            "stone": ("b0", 7),
            "flint": ("b1", 5)
        }
    def getID(itemname: str):
        return\
        ItemMaps.allItems()["itemname"]\
        if itemname in ItemMaps.allItems().keys()\
        else None

