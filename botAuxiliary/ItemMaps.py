from termios import VT1


class ItemMaps:
    def allItems():
        return {
            # "item_name": ("itemid", value)
        }
    def allItemsReversed():
        return {v[0]: (k, v[1]) for k, v in ItemMaps.allItems().items()}
    
    def matchingValue(value: int):
        return {k: v for k, v in ItemMaps.allItems().items() if v[1] == value}

    def getID(itemname: str):
        return\
        ItemMaps.allItems()[itemname][0]\
        if itemname in ItemMaps.allItems()\
        else None
    
    def getName(itemID):
        return\
        ItemMaps.allItemsReversed()[itemID][0]\
        if itemID in ItemMaps.allItems()\
        else None
