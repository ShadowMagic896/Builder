"""
Runs small command script to generate project dependencies
"""

import os


os.system("py -m pipdeptree > requirements.txt")
