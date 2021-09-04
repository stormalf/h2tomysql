#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os

__version__ = "1.0.0"

#constants
DATABASE = "DATABASE"
STATEMENT = "STATEMENT"
COMMENT = "COMMENT"
SEQUENCE = "SEQUENCE"
TABLE = "TABLE"
INDEX = "INDEX"
VIEW = "VIEW"
KEY = "KEY"

# to store useful information on each statement
class Token():
    def __init__(self, typetoken, stm, tokens, id, key, value):
        self.typetoken = typetoken
        self.stm = stm
        self.value = value
        self.tokens = tokens
        self.id = id
        self.key = key

    def __repr__(self): 
        return repr(f'type: {self.typetoken}, statement: {self.stm} tokens: {self.tokens} id: {self.id}, key: {self.key}, value: {self.value}')


# main function that parse h2file and create the mysql script in output
def main(argList):
    h2file = argList[0]
    mysqlfile = argList[1]
    isOk, isError, statements, sequences, comments, database, tables, alter, foreign, index, view = parseFile(h2file)
    createMysqlScript(mysqlfile, statements, sequences, comments, database, tables, alter, foreign, index, view)
    return isOk

#createMySqlScript removes the h2 specific syntax and replace by mysql syntax before writing in the output file
def createMysqlScript(mysqlfile, statements, sequences, comments, database, tables, alter, foreign, index, view):
    databasename = ""
    with open(mysqlfile, "w") as f :
        for stm in statements:
            if stm in database:
                databasename = database[stm].id + "."
            temptoken = statements[stm]
            line = temptoken.stm
            #mysql doesn't accept some keywords and the row size is also limited to 65535 (but text are not included on this limit size)
            #that's why we remove the keywords and replace some value by their equivalent to avoid the limit of 65535.
            #it's not possible to know all the configuration, specific needs concerning tables should be implemented here
            if stm in tables:
                line = line.replace('CACHED', '')
                line = line.replace('VARCHAR(2147483647)', 'LONGTEXT')
                line = line.replace('VARCHAR(4000)', 'TEXT(4000)')
                line = line.replace('VARCHAR(20000)', 'TEXT(20000)')
                line = line.replace('VARCHAR(10000)', 'TEXT(10000)')
                # for the create table retrieve the increment value to use if not found set to 1
                isSeqFound = False
                for seq in sequences:
                    if sequences[seq].id in line:
                        idvalue = sequences[seq].value
                        isSeqFound = True
                    else:
                        idvalue = 1
                #remove all information concerning sequence is not allowed in mysql        
                idx1 = line.index('DEFAULT (NEXT VALUE FOR') - 1
                idx2 = line[idx1:].index(',')
                #print(idx1, idx2)
                removeline = line[idx1: idx1 + idx2]
                #print(removeline)
                #print(line)
                line = line.replace(removeline, ' NOT NULL AUTO_INCREMENT')
                lastparen = line.rfind(")")
                #add the primary key information before the ending ")" and adds after that the AUTO_INCREMENT = value
                isFound = False
                # for alt in alter:
                #     if alter[alt].id in line and "PRIMARY KEY" in alter[alt].stm:
                #         isFound = True
                #         key = alter[alt].key
                #         line = line[:lastparen] + ", PRIMARY " + key + " )"  
                #case of no alter table to define the primary key but sequence found it means that we should add the primary key
                if not isFound and isSeqFound:
                    key = tables[stm].key
                    line = line[:lastparen] + ", PRIMARY KEY(" + key + ") )" 
                line = line.rstrip() + " AUTO_INCREMENT = " + str(idvalue) 
            #remove the database name before the index name    
            if stm in index:
                line = line.replace(databasename, '', 1)
            #remove FORCE keyword not allowed in mysql for views
            if stm in view:
                line = line.replace('FORCE', '')       
            #remove CACHED keyword not allowed in mysql for foreign keys    
            if stm in foreign:         
                idx1 = line.index('ADD CONSTRAINT')
                #idx2 = line.index('FOREIGN KEY')
                line = line[:idx1] + line[idx1:].replace(databasename, '', 1)
                line = line.replace('NOCHECK', '')
            #write only if it's not a create sequence neither a alter table with primary key neither a comment
            # comment in mysql script seems to accept # instead of common --    
            if 'END //' in line:
                f.write(line + "\n")
            elif stm not in sequences and stm not in alter and line != "" and stm not in comments:
                f.write(line + ";\n")
        #do stuff
    return

def parseFile(h2file):
    isSuccess = True
    error = ""
    allcontent= ""
    sequences = []
    refs_sequences = []
    dSequences, dStatements, dComments, dDatabase = {}, {}, {}, {}
    dTables, dAlter, dIndex, dView, dForeign = {}, {}, {}, {}, {}
    try:
        with open(h2file, "r") as f :
            #create blocks
            for line in f:
                allcontent = allcontent + line
        statements = allcontent.replace("\n", " ").split(";")
        #print(statement)
        for i, stm in enumerate(statements):
            stm = stm.strip()
            isSequence, isCreateSequence, idsequence, idvalue, tokens = checkIfSequences(stm)
            dStatements[i]= Token(STATEMENT, stm, tokens, " ", " ", 0)
            if isCreateSequence:
                sequences.append(stm)
                #print(f' {idsequence} {idvalue} {tokens}')
                dSequences[i] = Token(SEQUENCE, stm, tokens, idsequence, " ", idvalue)
                #iseq = iseq + 1
                continue

            # if isSequence and not isCreateSequence:
            #     refs_sequences.append(stm)
            #     drefSequences[i] = Token(STATEMENT, stm, tokens, " ", " ", 0)
            #     #iref = iref + 1
            
            if not isCreateSequence:
                isComment, tokens = checkIfComment(stm)
                if isComment:
                    dComments[i] = Token(COMMENT, stm, tokens, " ", " ", 0)
                    #icom = icom + 1
                    continue

            if not isComment: 
                isDatabase, tokens, iddb = checkIfDatabase(stm)
                if isDatabase:
                    dDatabase[i] = Token(DATABASE, stm, tokens, iddb, " ", 0 )
                    #idb = idb + 1
                    continue

            if not isDatabase:
                isTable, tokens, idtable, idkey = checkIfTable(stm) 
                if isTable:
                    dTables[i] = Token(TABLE, stm, tokens, idtable, idkey, 0)    
                    #itab = itab + 1 
                    continue

            if not isTable:
                isAlter, tokens, idalter, idkey = checkIfAlter(stm)
                if isAlter:                                              
                    dAlter[i] = Token(KEY, stm, tokens, idalter, idkey, 0)
                    #ialt = ialt + 1
                    continue
            if not isAlter:
                isIndex, tokens, idindex, idkey = checkIfIndex(stm)
                if isIndex:
                    dIndex[i] = Token(INDEX, stm, tokens, idindex, idkey, 0)
                    #iind = iind + 1
                    continue
            if not isIndex:
                isView, tokens, idview = checkIfView(stm)
                if isView:
                    dView[i] = Token(VIEW, stm, tokens, idview, " ", 0)
                    #iview = iview + 1
                    continue                
            if not isView:
                isForeign, tokens, idforeign, idkey = checkIfForeign(stm)
                if isForeign:
                    dForeign[i] = Token(KEY, stm, tokens, idforeign, idkey, 0 )    
        printTokenResult(dSequences, dComments, dDatabase, dTables, dAlter, dIndex, dView)
    except IOError:
        print("Error during reading " + h2file)
        isSuccess = False   
        return isSuccess, error, dStatements                
    return isSuccess, error, dStatements, dSequences, dComments, dDatabase, dTables, dAlter, dForeign, dIndex, dView

def checkIfSequences(stm):
    isSequence = False
    isCreateSequence = False
    idsequence = " "
    idvalue = 1
    tokens = createTokenList(stm)
    if 'SEQUENCE' in tokens:
        isSequence = True
        if len(tokens) >= 5: 
            if tokens[1] == 'SEQUENCE':
                #print(tokens)
                idsequence = tokens[2]
                idValue = tokens[5]
                isCreateSequence = True
    return isSequence, isCreateSequence, idsequence, idvalue, tokens

def printTokenResult(dSequences, dComments, dDatabase, dTables, dAlter, dIndex, dView):
    print("sequences :")
    print(dSequences)
    print("_________________________________")
    # print("sequences references:")
    # print(drefSequences)
    # print("_________________________________")        
    # print("comments :")
    # print(dComments)
    # print("_________________________________")        
    # print("database: ")
    # print(dDatabase)
    # print("_________________________________")        
    print("tables :")
    print(dTables)
    print("_________________________________")        
    print("alter : ")
    print(dAlter)
    print("_________________________________")        
    # print("index : ")
    # print(dIndex)
    # print("_________________________________")       
    # print("view : ")
    # print(dView)
    # print("_________________________________")   

def checkIfComment(stm):
    isComment = False
    tokens = createTokenList(stm)
    if '--' in tokens:
        if len(tokens) >= 1: 
            if tokens[0] == '--':
                #print(tokens)
                isComment = True
    return isComment, tokens   


def checkIfDatabase(stm):
    isDatabase = False
    tokens = createTokenList(stm)
    iddb = " "
    if 'DATABASE' in tokens:
        if len(tokens) >= 3: 
            if tokens[1] == 'DATABASE':
                #print(tokens)
                isDatabase = True
                iddb = tokens[2]
    return isDatabase, tokens, iddb   


def checkIfTable(stm):
    isTable = False
    tokens = createTokenList(stm)
    #print(tokens)
    idtable = " "
    idkey = " "
    if 'TABLE' in tokens:
        if len(tokens) >= 4: 
            if tokens[0] == 'CREATE':
                #print(tokens)
                isTable = True
                idtable = tokens[3].replace("(", "")
                idx1 = stm.index('DEFAULT (NEXT VALUE FOR')
                idx2 = stm[:idx1].rfind("(")
                idx3 = stm[:idx1].rfind(",")
                maxidx = max(idx2, idx3) + 1
                #print(idx1, idx2)
                substring = stm[maxidx: maxidx + idx2].strip()
                subtoken = substring.split(" ")
                idkey = subtoken[0]
    return isTable, tokens, idtable, idkey


def checkIfAlter(stm):
    isAlter = False
    tokens = createTokenList(stm)
    #print(tokens)
    idalter = " "
    idkey = " "
    if 'TABLE' in tokens:
        if len(tokens) >= 8: 
            if tokens[0] == 'ALTER' and "PRIMARY" in tokens:
                #print(tokens)
                isAlter = True
                idalter = tokens[2]
                idkey = tokens[7]
    return isAlter, tokens, idalter, idkey


def checkIfForeign(stm):
    isForeign = False
    tokens = createTokenList(stm)
    #print(tokens)
    idforeign = " "
    idkey = " "
    if 'TABLE' in tokens:
        if len(tokens) >= 8: 
            if tokens[0] == 'ALTER' and "PRIMARY" not in tokens:
                #print(tokens)
                isForeign = True
                idforeign = tokens[2]
                idkey = tokens[7]
    return isForeign, tokens, idforeign, idkey

def checkIfIndex(stm):
    isIndex = False
    tokens = createTokenList(stm)
    #print(tokens)
    idindex = " "
    idkey = " "
    if 'INDEX' in tokens:
        if len(tokens) >= 5: 
            if tokens[0] == 'CREATE':
                #print(tokens)
                isIndex = True
                idindex = tokens[2]
                idkey = tokens[4]
    return isIndex, tokens, idindex, idkey  


def checkIfView(stm):
    isView = False
    tokens = createTokenList(stm)

    idview = " "
    if 'VIEW' in tokens:

        if len(tokens) >= 4: 
            #print(tokens)
            if tokens[0] == 'CREATE':
                #print("new" + tokens[0])
                isView = True
                idview = tokens[3]
    return isView, tokens, idview  

def createTokenList(line):
    tokens = line.split(" ")
    return tokens


def manageError():
    print("two arguments required!")   
    h2tomysql_print_help()

#this function prints the help
def h2tomysql_print_help():
    print("H2ToMysql is a python3 program that helps to generate a sql script for import into mysql database.")
    print("H2ToMysql uses Python3")
    print("H2ToMysql tested with mysql 8.0.25")
    print("_____________________________________________________________________________________________________")
    print("WARNING : it doesn't deal with all cases, probably you need to adapt the code to your specific needs!")
    print("_____________________________________________________________________________________________________")
    print("For linux and linux-like OS that have the pre-requisites")
    print("Usage: h2tomysql [options] fromfile tofile")
    print("Required : fromfile  is the file that has the h2 script")
    print("Required : tofile    is the result file that will contain compliant mysql script")
    print("Options:")
    print("-V, --version        Display version number of PyToC compiler")
    print("-H, --help           Display this help")
    print("__________________________________________")
    print("Enjoy!")


#starting code
if __name__ == "__main__":
    argList = []
    argList = sys.argv[1:]
    nbarg = len(argList)
    isOk = False
    if nbarg == 0:
        manageError()
    else:        
        argFirst = argList[0]
        if argFirst.lower() == '--help' or argFirst.lower() == '-h':
            h2tomysql_print_help()
        elif argFirst.lower() == '--version' or argFirst.lower() == '-v':
            print("H2ToMysql version " + __version__)    
        else:                        
            if nbarg != 2:
                manageError()
            else:        
                if not os.path.isfile(argFirst): 
                    print(f"File {argFirst} not found")
                else:                    
                    isOk = main(argList)
                    if isOk:
                        print("done!")
                    else:
                        print("error occurred see the log!")                        