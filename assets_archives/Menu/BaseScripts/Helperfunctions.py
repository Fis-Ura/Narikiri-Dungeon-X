import os.path
import json
import subprocess
import shutil
import itertools
import pandas as pd
import pygsheets
from os import fdopen, remove
import re

class Helper:
    
    #Initialize object
    def __init__(self):
        
        self.basePath = os.path.abspath(os.path.dirname(__file__))
        self.tblName = "sjis.tbl"
        
        
        self.loadTable()
        
    def getJsonBlock_SPLS(self,blockDesc):
        return [ele for ele in self.dataItems if ele['BlockDesc'] == blockDesc][0]
    
    def getJsonBlock_Other(self,blockDesc):
        return [ele for ele in self.otherItems if ele['BlockDesc'] == blockDesc][0]
    
    def showSections(self,blockDesc):
        
        blockSections = self.getJsonBlock_SPLS(blockDesc)
        sectionsInfos = [ [ele['SectionId'], ele['SectionDesc']] for ele in blockSections['Sections']]
        
        #Print the sections on the screen
        for sectionId, sectionDesc in sectionsInfos:
            print("{}. {}".format(sectionId, sectionDesc))
        print("\n")
       
        
        
    def parseGoogleSheet(self):
            
        dfLines = [ele.split("\n") for ele in self.dfData['English'] ]
        lines = list(itertools.chain(*dfLines))
        
        
        finalList = []
        for index,row in self.dfData.iterrows():
            
            block = row['English']
            lines = block.split("\n")
            
            textOffset  = lines[0][lines[0].find("$")+1:].replace("\n","")
            pointer     = lines[1][lines[1].find("$")+1:].replace(")\n","")
            text        = block[block.find(")")+1:]
            finalList.append( [block,text, textOffset, pointer])
        
        
        
        
        
        
        return finalList
    

    def parseTextFile(self, fileName):
    
        fread = open(os.path.join(self.basePath,"abcde", fileName),encoding="utf-8", mode="r")
        lines = fread.readlines()
        
        start=0
        startText=0
        end=0
        mylist=[]
        dfLines = pd.DataFrame(lines, columns=["Text"])
        finalList=[]
        
        for i,line in enumerate(lines):
            
            if "//Text " in line:
                start=i
                textOffset = line[line.find("$")+1:].replace("\n","")
                
               
                    
            if "WRITE" in line:
                pointer = line[line.find("$")+1:].replace(")\n","")
                startText=i+1
                
                    
            if "// current" in line:  
                text = "".join(dfLines['Text'][startText:i])
                endOffset = line[line.find("$")+1:].replace("\n","")
                #print("startText : {}   i: {}".format(startText, i))
                ele = ["".join(dfLines['Text'][start:i]), text, textOffset, endOffset, pointer]
                finalList.append(ele)
        
        return finalList
    
    def cleanDump(self, dumpFile):
        
  
        f = open(os.path.join(self.basePath,dumpFile), mode="r", encoding="utf-8")
        destFile = open(os.path.join(self.basePath,dumpFile.replace(".txt","")+"_cleaned.txt"), mode="w", encoding="utf-8")
        for line in f:
            if "#JMP(" not in line:
                line = line.replace("#HDR($-{}) // Difference between ROM and RAM addresses for pointer value calculations".format(self.PointerHeader),"")
                line = line.replace("#ACTIVETBL(Table_0) // Activate this block's starting TABLE","")
                line = line.replace("#W32(","#WRITE(ptr,")
                if "//BLOCK #" in line:
                    line = ""
                if "//POINTER " in line:
                    line = "//Text "+line.split(" ")[-1]
                    
                #if "<$81>@" in line:
                #    line = line.replace("<$81>@"," ")
                destFile.write(line)
            
        f.close()
        destFile.close()
        self.removeBlankPointerData(dumpFile.replace(".txt","")+"_cleaned.txt")
        os.remove(os.path.join(self.basePath,dumpFile))
        
    def createScript(self, fileName, n, startPoint, step, nbObject):
    
        blockText = """
#BLOCK NAME:	Items_{}
#TYPE:		NORMAL
#METHOD:		          POINTER_RELATIVE
#POINTER ENDIAN:		LITTLE
#POINTER TABLE START:	${}
#POINTER TABLE STOP:	${}
#POINTER SIZE:		$04
#POINTER SPACE:		$00
#ATLAS PTRS:		Yes
#BASE POINTER:		$-{}		//add $FF000 to each pointer to get
#TABLE:			{}	//the string address
#SORT OUTPUT BY STRING ADDRESS:        Yes
#COMMENTS:		No
#END BLOCK
"""

        pathFile = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(pathFile,fileName), "w") as f:
            f.write("#GAME NAME:			Tales of destiny 2")
            
            for x in range(n):
                
                start = hex(int(startPoint,16) + x*step)[2:].upper()
                end   = hex(int(startPoint,16) + 4*nbObject-1 + x*step)[2:].upper()
                f.write(blockText.format(x+1, start, end, self.PointerHeader, self.tblName))
        

    def runscript(self, sourceName, file):
    
        args = ["perl", "abcde.pl", "-m", "bin2text", "-cm", "abcde::Cartographer", os.path.join(self.basePath,sourceName), file+"_script.txt", file+"_dump", "-s"]
        listFile = subprocess.run(
            args,
            cwd= os.path.abspath(os.path.dirname(__file__)),
            )
    

    def writeColumn(self,finalList, googleId):
        
        sh = self.gc.open_by_key(googleId)
    
        #Look for Dump sheet 
        wks = sh.worksheet('title','Dump')
          
        #update the first sheet with df, starting at cell B2. 
        df=pd.DataFrame({"Japanese":finalList, "English":finalList})
        wks.set_dataframe(df,(1,0))
    
    def getGoogleSheetTranslation(self,googlesheetId, sheetName):
        
        sh = self.gc.open_by_key(googlesheetId)
        sheets = sh.worksheets()
        
        idSheet = [ ele.index for ele in sheets if ele.title == sheetName ][0]
        if idSheet != None:
            wks = sh[idSheet]
            
            df = pd.DataFrame(wks.get_all_records())
            
            #with open("test.txt",encoding="utf-8", mode="w") as f:
            #    f.write(translationsText)
            self.dfData = df
        else:
            print("Cannot find the sheet name in the google sheet")
            return "No"
    

    def removeBlankPointerData(self,fileName):
    
        fread = open(os.path.join( self.basePath,"abcde", fileName),encoding="utf-8", mode="r")
        fwrite = open(os.path.join( self.basePath,"abcde", "w"+fileName),encoding="utf-8", mode="w")
        
        lines = fread.readlines()
        indexStart = [i for i,line in enumerate(lines) if "FFFFFFFFFFF01000" in line] 
        indexComp = [list(range(i,i+5)) for i in indexStart]
        indexComp = list(itertools.chain.from_iterable(indexComp))
        
        for i,line in enumerate(lines):
            if i not in indexComp:
                
                fwrite.write(line)
                
        fread.close()
        fwrite.close()
        
        shutil.copyfile( os.path.join(self.basePath, "abcde","w"+fileName), os.path.join(self.basePath, "abcde",fileName))
    
    def getHeader(self):
        headerTxt="""#VAR(Table_0, TABLE)
#ADDTBL("{}", Table_0)

//BLOCK #000 NAME:
#ACTIVETBL(Table_0) // Activate this block's starting TABLE
#VAR(ptr, CUSTOMPOINTER)
#CREATEPTR(ptr, "LINEAR", $-{}, 32)

""".format(os.path.join(self.basePath, "abcde", self.tblName), self.PointerHeader)
    
    
        return headerTxt

    def loadTable(self):
    
        with open(os.path.join(self.basePath,self.tblName), encoding="utf-8", mode="r") as tblfile:
            lines=tblfile.readlines()
            
        df = pd.DataFrame(lines, columns=['Value'])
        
        df['Value'] = [re.sub(r'\n$', '', ele) for ele in  df['Value']]
        df['Split'] = df['Value'].str.split("=")
        df['Hex']   = df['Split'].apply(lambda x: x[0])
        #df['Text']  = df['Split'].apply(lambda x: x[-1])
        df['Text']  = df['Split'].apply(lambda x: x[-1].replace("[END]\\n","[END]").replace("\\n","\n"))
        df.loc[ df['Text'] == "", 'Text'] = "="
        df.loc[ df['Hex'] == "/00","Hex"] = "00"
        
        df['NbChar']= df['Text'].apply(lambda x: len(x))
        listKeys = df['Text'].tolist()
        listValue = df['Hex'].tolist()
        mydict = {listKeys[i]: listValue[i] for i in range(len(listKeys))} 
        keys = keys=sorted(list(mydict.keys()),key=lambda x: len(x))[::-1]
        
        self.keys = keys
        self.mappingTbl = mydict

    def findall(self,p, s):
        '''Yields all the positions of
        the pattern p in the string s.'''
        i = s.find(p)
        while i != -1:
            yield i
            i = s.find(p, i+1)
    
    def countBytes(self,text):
        
        out=[]
        base=text
        for k in self.keys:
               
            if k in base:
                
                #nb = len(re.findall(k.replace("?","\?").replace("[","\["), v))
                nb = len([i for i in self.findall(k, base)])
          
                
                base=base.replace(k,'')
                #print(base)
                out.append(self.mappingTbl[k]*nb)
                
        res = len("".join(out))/2
        
        return res

    def cleanData(self):
        
        self.dfData['English'] = self.dfData['English'].apply(lambda x: re.sub('\[END]$', '[END]\n', x))
        self.dfData['English'] = self.dfData['English'].str.replace("\r","")


    def createAdjustedBlock(self):
    
        #keys = [x for x in keys if not (x.isdigit() or x[0] == '-' and x[1:].isdigit())]
        self.dfData['TranslatedText'] = self.dfData['English'].apply(lambda x: x.split(")",1)[-1][1:])
        #dfData['NbBytes'] = dfData['TranslatedText'].apply( lambda x: countBytes( keys, mappingTbl, x))
        #dfData.to_excel("test.xlsx")
        
        
        sectionText=""
        
       
        for index,row in self.dfData.iterrows():
            textAdd=""
            v = row['TranslatedText']
     
            
            nb = self.countBytes(v)
            
            
            if (self.offset + nb > self.currentEnd):
                print("Sub Section start:            {}".format(hex(int(self.currentStart))))
                print("Sub Section original end:     {}".format(hex(int(self.currentEnd))))
                print("Sub Section translated end:   {}\n".format(hex(int(self.offset))))
                print("Overlapp, jump needed")
                print("Offset: {}".format(hex(int(self.offset))))
                
                #print("endInt: {}".format(endInt))
                self.currentMemoryId+= 1
                print("Text to insert : "+v)
                print("BankId: "+str(self.currentMemoryId))
                
                #Go grab a bank of memory
                newbank = self.dfBanks[ (self.dfBanks['Id'] == self.currentMemoryId) & (self.dfBanks['File'] == self.File)]
                self.offset = int(newbank['TextStart'].tolist()[0], 16)
    
                self.currentEnd = int(newbank['TextEnd'].tolist()[0], 16)
                textAdd += "#JMP(${})\n".format(newbank['TextStart'].tolist()[0])
                
                self.currentStart = self.offset
                
            
            self.offset += nb
                
                
                
            textAdd += "{}\n".format( row['English'])
            sectionText += textAdd
                
        print("Final Section start:            {}".format(hex(int(self.currentStart))))
        print("Final Section original end:     {}".format(hex(int(self.originalSectionEnd))))
        print("Final Section translated end:   {}\n".format(hex(int(self.offset))))
        
        self.currentStart = self.offset
        
        return sectionText
        
    def createBlock(self,blockDesc):
        
        #gc = pygsheets.authorize(service_file="gsheet.json")
        
        #Go grab the TextStart for the jump
        block = self.getJsonBlock_SPLS(blockDesc)
        self.File = block['File']
        self.PointerHeader = block['PointerHeader']
        self.createAllBanks()
        
        sections = block['Sections']
        lastSection = max([ele['SectionId'] for ele in sections])
        #Variables for adjusting overlapping
        textStart = [ele['TextStart'] for ele in sections if ele['SectionId'] == 1][0]
        textEnd = [ele['TextEnd'] for ele in sections if ele['SectionId'] == lastSection][0]
        self.currentStart  = int(textStart, 16)
        self.currentEnd    = int(textEnd, 16)
        self.offset = int(textStart,16)
        
        
        #Add the first jump
        jumpText = "#JMP(${})\n".format(textStart)
        
        #Grab some infos for each sections
        sectionsList = [ (ele['SectionId'], ele['SectionDesc'], ele['GoogleSheetId']) for ele in sections ]
        
        #Create a block of text with each section
        blockText = ""
        blockText += jumpText
      
        
        for sectionId, sectionDesc, googleId in sectionsList:
            
            blockText += "//Section {}\n\n".format(sectionDesc)
            self.originalSectionEnd = int([ele['TextEnd'] for ele in sections if ele['SectionId'] == sectionId][0],16)
            if googleId != "":
              
                
                #Grab the text from google sheet
                self.getGoogleSheetTranslation(googleId, sectionDesc)
                self.cleanData()
                
                sectionText = self.createAdjustedBlock()
                
                #Add the result to the section
                blockText += sectionText.replace("\r","")
        
        print("Max Block End               :   {}".format(hex(int(textEnd, 16))))
        return block['BlockDesc'], blockText

    def createAtlasScript_Block(self,blockDesc):
        

        block = self.createBlockAll(blockDesc)
       
        header = self.getHeader()
        with open(os.path.join(self.basePath,"abcde", "TODDC_"+blockDesc+"_Dump.txt"),encoding="utf-8", mode="w") as finalScript:
            finalScript.write(header + block)
    
    def reinsertText_Block(self,blockDesc):
    
        #Copy the original file
        fileName = os.path.basename(self.File) 
        
        if blockDesc != "Synopsis" and fileName != "00014.bin":
            shutil.copyfile( os.path.join(self.basePath,self.File), os.path.join(self.basePath,"abcde",fileName))
        
        #Run Atlas in command line
        #blockDesc = [ele['BlockDesc'] for ele in self.dataItems if ele['BlockDesc'] == blockDesc][0]
        
        args = ["perl", "abcde.pl", "-m", "text2bin", "-cm", "abcde::Atlas", fileName, "TODDC_"+blockDesc+"_Dump.txt"]
        listFile = subprocess.run(
            args,
            cwd= os.path.join(self.basePath, "abcde"),
            )
        
        #Copy the new SLPS back to Google drive
        #print( "Source: " + os.path.join(path, "SLPS_258.42"))
        #print( "Destination: " + os.path.join(path,"..","..", slpsName))
        shutil.copyfile( os.path.join(self.basePath,"abcde", fileName), os.path.join(self.basePath,"..", fileName))
    
    def createAllBanks(self):
        
       

        #For each block, pick the first and last Offset
        listBlock = [ [ ele['BlockDesc'], ele['Sections'][0]['TextStart'], ele['Sections'][-1]['TextEnd'], ele['File']] for ele in self.dataItems if ele['File'] == self.File]
        dfBase = pd.DataFrame(listBlock, columns=['BlockDesc','TextStart','TextEnd', 'File'])
        print(dfBase)
        
        #Add the 3 original memory banks
        self.dfBanks = dfBase.append(self.dfBanks)
        self.dfBanks = self.dfBanks[ self.dfBanks['File'] == self.File]
        self.dfBanks = self.dfBanks.reset_index(drop=True)
        self.dfBanks['Id'] = self.dfBanks.index + 1
        print( self.dfBanks)
    
    
    def createBlockAll(self, blockDesc):
            
        if blockDesc == "All":
            self.File = "abcde/SLPS_original/SLPS_258.42"
            self.PointerHeader = "FF000"
        else:
            block = self.getJsonBlock_SPLS(blockDesc)
            self.File = block['File']
            self.PointerHeader = block['PointerHeader']
        self.createAllBanks()
        
        #tbl dataframe to use
        self.loadTable()
        
        #Variables for adjusting overlapping
        memoryId=1
        bank = self.dfBanks[ self.dfBanks['Id'] == memoryId]
        
        banksNotEmpty = self.dfBanks[ self.dfBanks['BlockDesc'] != ""]
        lastbank = banksNotEmpty[banksNotEmpty['Id'] == banksNotEmpty['Id'].max()]
        
        textStart = bank['TextStart'][0]
        finalEnd = lastbank['TextEnd'].tolist()[0]
        self.currentStart  = int(textStart, 16)
        self.currentEnd    = int(bank['TextEnd'][0], 16)
        self.offset = self.currentStart
        
        #First Jump
        jumpText = "#JMP(${})\n".format(textStart)
        allText = jumpText
        
        #Loop over all block
        dfBlock = self.dfBanks[ self.dfBanks['BlockDesc'] != ""]
        #print(self.dfBanks)
        for index, row in dfBlock.iterrows():
            
            
            
            print("Block: {}".format(row['BlockDesc']))
            sections = [ele['Sections'] for ele in self.dataItems if ele['BlockDesc'] == row['BlockDesc']][0]
            #print(sections)
            sectionsList = [ (ele['SectionId'], ele['SectionDesc'], ele['GoogleSheetId']) for ele in sections ]
            
            #Create a block of text with each section
            blockText = ""
            for sectionId, sectionDesc, googleId in sectionsList:
            
                blockText += "//Section {}\n\n".format(sectionDesc)
                self.originalSectionEnd = int([ele['TextEnd'] for ele in sections if ele['SectionId'] == sectionId][0],16)
                if googleId != "":
                    print(sectionDesc)
                    print("Google Sheet : {}".format(sectionDesc))
                    self.getGoogleSheetTranslation(googleId, sectionDesc)
                    self.cleanData()
                    
                    print("Create Adjusted block : {}".format(sectionDesc))
                    sectionText = self.createAdjustedBlock()
                    
                    #Add the result to the section
                    blockText += sectionText.replace("\r","")
                    
            allText += blockText
            
        print("Max Block End               :   {}".format(hex(int(finalEnd, 16))))
        return allText
            
    
    def createBlock_Multi(self, blockDesc):
        
        #tbl dataframe to use
        self.loadTable()
        
        #tbl dataframe to use
        #print(self.otherItems)
        block = self.getJsonBlock_Other(blockDesc)
        self.PointerHeader = block['PointerHeader']
        googleId = block['GoogleSheetId']
        self.File = block['FilePointer']
        print(self.File)
        
        #Load the google sheet data with all text, pointers
        self.getGoogleSheetTranslation(googleId, blockDesc)
        self.cleanData()
        finalList = self.parseGoogleSheet()
        dfFinal = pd.DataFrame(finalList, columns=["TextOffset", "Text", "TextOffset", "Pointer"])
        dfFinal.to_excel("dfFinal.xlsx")
        
        #Create the script as is in the original file (first section file)
        allText = "\n".join(self.dfData['English'].tolist())  
        jumpText = "#JMP(${})\n".format(block['Sections'][0]['TextStart'])
        header = self.getHeader()
        with open(os.path.join(self.basePath,"abcde", "TODDC_{}_Dump.txt".format(blockDesc)),encoding="utf-8", mode="w") as finalScript:
            finalScript.write(header + jumpText + allText)
            
            
        #Run the script on the file to create a temp file
        self.reinsertText_Block(blockDesc)
        
        #Extract again the text using Abcde script
        self.extract_Block(blockDesc)
        self.cleanDump("TODDC_{}_Dump_Temp.txt".format(blockDesc))

        
        #Store in memory the number of bytes, length of all the text
        listText = self.parseTextFile("TODDC_{}_Dump_Temp_Cleaned.txt".format(blockDesc))
        dfTemp = pd.DataFrame(listText, columns=["Block", "Text", "TextOffset", "EndOffset", "Pointer"])
        dfTemp["Length"] = dfTemp['EndOffset'].apply(lambda x : int(x, 16)) - dfTemp['TextOffset'].apply(lambda x : int(x,16))
        dfTemp["TextOffsetInt"] = dfTemp["TextOffset"].apply(lambda x: int(x,16))
  
        #dfFinal.to_excel("final.xlsx")
        
        dfTemp.to_excel("temp_Prep.xlsx")
        
        #Find the cutting line and separate the text in the different file
        sections = [[ele['SectionId'], ele['File'], ele['PointerHeader'], ele['TextStart'], ele['TextEnd']] for ele in block['Sections']]
        dfSections = pd.DataFrame(sections, columns=['SectionId','File','PointerHeader', 'TextStart', 'TextEnd'])
        
        lower=0
        dfTemp['File'] = ''

        for index,row in  dfSections.iterrows(): 
        
            #Find the last text to insert in this section
            file = row['File']
            pointerHeaderInt = int(row['PointerHeader'], 16)
       
            print("File: {}".format(file))
        
            
            textStartInt = int(row['TextStart'], 16)
            textEndInt = int(row['TextEnd'], 16)
            

            dfTempCalcul = dfTemp[ dfTemp['File'] == ""]
            dfTempCalcul.loc[:,"TextOffsetCumul"] = dfTempCalcul['Length'].cumsum() + [textStartInt]
            dfTemp.loc[ dfTemp['File'] == "", 'TextOffsetCumul'] = dfTempCalcul["TextOffsetCumul"]
            
            dfTemp.loc[ dfTemp['TextOffsetCumul'] < textEndInt, 'File'] =  file
            dfTemp.loc[ dfTemp['TextOffsetCumul'] < textEndInt, 'PointerHeaderInt'] =  pointerHeaderInt
            
        dfTemp.to_excel("temp.xlsx")   
        dfTemp.loc[:,"NewTextOffSetInt"] = dfTemp["TextOffsetCumul"] - dfTemp["Length"]
        dfTemp["NewTextSum"]   = [hex(ele)[2:].capitalize() for ele in dfTemp["NewTextOffSetInt"] + dfTemp["PointerHeaderInt"].astype(int) ]
        dfTemp["NewPointerValue"]   = [ ele[4:6] + ele[2:4] + ele[0:2] for ele in dfTemp["NewTextSum"]]
        
        
        
        
        for file in dfTemp["File"].unique().tolist():
            
            #Create a script for reinserting the text in each file
            dfText = dfTemp[ dfTemp["File"] == file]
            
            print(dfText)
            fileName = fileName = os.path.basename(file) 
            allText = "\n".join(dfText['Block'].tolist())  
            
            textStart = hex(dfText['NewTextOffSetInt'].min())[2:]
           
            jumpText = "#JMP(${})\n".format(textStart)
            
            self.PointerHeader = hex(int(dfText['PointerHeaderInt'].tolist()[0]))[2:].capitalize()
            
            print(self.PointerHeader)
            header = self.getHeader()
            with open(os.path.join(self.basePath,"abcde", "TODDC_{}_Dump.txt".format(blockDesc)),encoding="utf-8", mode="w") as finalScript:
                finalScript.write(header + jumpText + allText)
               
            if file != block['FilePointer']:
                with open(os.path.join(self.basePath,"abcde", "TODDC_{}_Dump.txt".format(blockDesc)),encoding="utf-8", mode="w") as finalScript:
                    
                    for line in (header + jumpText + allText).splitlines(True):
                    
                        if not "#WRITE" in line:
                            finalScript.write(line)
                    
            #Run the script on the file to create a temp file
            self.File = file
            
           
            self.reinsertText_Block(blockDesc)
    
            
            #Update the pointers
            if file != block['FilePointer']:
               self.updatePointersBaseFile(block['FilePointer'], dfTemp[ dfTemp['File'] == file])
            
    def updatePointersBaseFile(self, filePointerPath, dfTemp):
        
        filePointer = os.path.basename(filePointerPath) 
        hexString = "00".join(dfTemp['NewPointerValue'].tolist())
        arrayHex = bytearray.fromhex(hexString)
        pointerTableOffset = int(dfTemp['Pointer'].tolist()[0], 16)
        print("PointerOffset: {}".format(pointerTableOffset))
        
        #Open the file
        with open(os.path.join(self.basePath,"abcde", filePointer), mode="r+b") as f:
            f.seek(pointerTableOffset)
            f.write(arrayHex)
            
            
    def createAtlasScript_All(self):
        

        allText = self.createBlockAll("All")
       
        header = self.getHeader()
        with open(os.path.join(self.basePath,"abcde", "TODDC_All_Dump.txt"),encoding="utf-8", mode="w") as finalScript:
            finalScript.write(header + allText)

    
    def reinsertText_All(self, fileFull):
    
        #Copy the original SLPS file first
        shutil.copyfile( os.path.join(self.basePath,"abcde","SLPS_original","SLPS_258.42"), os.path.join(self.basePath,"abcde","SLPS_258.42"))
        
        
        args = ["perl", "abcde.pl", "-m", "text2bin", "-cm", "abcde::Atlas", "SLPS_258.42", "TODDC_All_Dump.txt"]
        listFile = subprocess.run(
            args,
            cwd= os.path.join(self.basePath, "abcde"),
            )
        
        shutil.copyfile( os.path.join(self.basePath,"abcde", "SLPS_258.42"), os.path.join(self.basePath,"..", "SLPS_258.42"))
        
    def extract_Block(self, blockDesc):
        
        #Copy the original file
        fileName = os.path.basename(self.File) 
        #shutil.copyfile( os.path.join(self.basePath,self.File), os.path.join(self.basePath,"abcde",fileName))
        
        #Run Atlas in command line
        #blockDesc = [ele['BlockDesc'] for ele in self.dataItems if ele['BlockDesc'] == blockDesc][0]
        
        args = ["perl", "abcde.pl", "-m", "bin2text", "-cm", "abcde::Cartographer", fileName, os.path.join("Script_Extraction","TODDC_{}_Script.txt".format(blockDesc)), "TODDC_{}_Dump_Temp".format(blockDesc), "-s"]
        listFile = subprocess.run(
            args,
            cwd= os.path.join(self.basePath, "abcde"),
            )
      
    
    
