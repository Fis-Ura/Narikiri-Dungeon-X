from HelperfunctionsNew import *
import sys
import os

if __name__ == "__main__":
    
    blockDesc = sys.argv[1]
    
    
    helper = Helper()
    herlper.get
    if blockDesc in ["Skit Name", "Synopsis", "Minigame"]:
        helper.createBlock_Multi(blockDesc)
        
    elif blockDesc != "All":
    

        
        print("Create the script based on google sheet")
        helper.createAtlasScript_Block(blockDesc)
        
        
        print("Create the SLPS for this block")
        helper.reinsertText_Block(blockDesc)
    else:
        
        helper.createAtlasScript_All()
        
        print("Create the SLPS for this block")
        helper.reinsertText_All(blockDesc)