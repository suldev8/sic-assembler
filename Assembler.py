import re
import instfile


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute

class literalsEntry:
    def __init__(self, name, value, address):
        self.name = name
        self.value = value
        self.address = address


symtable = []
LITTAB = []

started = "E "
text = "T "
# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))


def lookup(s):
    for i in range(0, symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1


def insert(s, t, a):
    symtable.append(Entry(s, t, a))
    return symtable.__len__() - 1

def insertToLittab(n,v,a):
    LITTAB.append(literalsEntry(n,v,a))
    return LITTAB

def init():
    for i in range(0, instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.opcode[i], instfile.token[i])
    for i in range(0, instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])


file = open('input.sic', 'r')
filecontent = []
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ''
startLine = True
type3 = instfile.inst.__len__()
datax = instfile.inst.__len__() + instfile.directives.__len__()
org_exist = False

index = False
programType = ''
output = []

endlocctr = 0

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000


def is_hex(s):
    if s[0:2].upper() == '0X':
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False


def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return 'EOF'
        elif filecontent[bufferindex] == '#':
            startLine = True
            while filecontent[bufferindex] != '\n':
                bufferindex = bufferindex + 1
            lineno += 1
            bufferindex = bufferindex + 1
        elif filecontent[bufferindex] == '\n':
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(filecontent[bufferindex])  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(filecontent[bufferindex][2:], 16)  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return ('NUM')
    elif filecontent[bufferindex] in ['+', '#', ',']:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return (c)
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == 'C') and (filecontent[bufferindex + 1] == '\''):
            bytestring = ''
            bufferindex += 2
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif filecontent[bufferindex] == '\'':  # a string can start with C' or only with '
            bytestring = ''
            bufferindex += 1
            while filecontent[bufferindex] != '\'':  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != '\'':
                    bytestring += ' '
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'STRING', bytestringvalue)  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == 'X') and (filecontent[bufferindex + 1] == '\''):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue) % 2 == 1:
                bytestringvalue = '0' + bytestringvalue
            bytestring = '_' + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(bytestring, 'HEX', bytestringvalue)  # should we deal with literals?
            tokenval = p
        else:
            p = lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine:
                    p = insert(filecontent[bufferindex].upper(), 'ID', locctr)  # should we deal with case-sensitive?
                    startLine = False
                else:
                    p = insert(filecontent[bufferindex].upper(), 'ID', -1)  # forward reference
            else:
                if (symtable[p].att == -1) and startLine:
                    symtable[p].att = locctr
                    startLine = False
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return symtable[p].token


def error(s):
    global lineno
    print('line ' + str(lineno) + ': ' + s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error('Syntax error')


def checkindex():
    global bufferindex, symtable, tokenval, index
    if lookahead == ',':
        match(',')
        if symtable[tokenval].att != 1:
            error('index register should be X')
        else:
            match('REG')
            return True
    return False

def inc_locctr(inc):
    global locctr, org_exist
    if org_exist:
        locctr = inc
    else:
        locctr += inc

def checkProgramSic():
    global programType
    if programType:
        error('syntax error: sic does not work with f1 and f2')
def checkLiterals(check):
    global locctr, pass1or2
    if (check == '='):
        match('ID')
        if lookahead == 'STRING':
            insertToLittab('=C'+symtable[tokenval].string,symtable[tokenval].att,locctr)
            match('STRING')
        elif lookahead == 'HEX':
            insertToLittab('=X'+symtable[tokenval].string,symtable[tokenval].att,locctr)
            match('HEX')
        return True
    else:
        return False

def printObjectCode(x):
    print(x)
# ============================== Parser starts here ==============================
def parse():
    sic()


def sic():
    global lookahead
    header()
    body()
    tail()


def header():
    global lookahead, locctr, tokenval, output, endlocctr, programType, started, text
    lookahead = lexan()
    programType = symtable[tokenval].string
    print(programType)
    match('ID')
    programName = tokenval

    match('ID')
    match('START')
    locctr += tokenval
    if pass1or2 == 1 :
        started += str(f'{locctr:06x}')
        text += str(f'{locctr:06x}') + " "

    if pass1or2 == 1:
        print('Pass 1:')
        print(f'{locctr:04x}')
    else:
        output.append('H')
        output.append(symtable[programName].string)
        output.append(f'{locctr:06x}')
        output.append(f'{locctr - endlocctr :06x}')
        #print(' '.join(output))
        print('\nPass 2:')

    match('NUM')


def body():
    global type3, org_exist, lookahead, locctr, text

    if lookahead == 'ID':
        match('ID')
        rest1()
        body()

    elif tokenval < type3 and tokenval > -1:
        stmt()
        body()
    elif symtable[tokenval].string == 'ORG':
        org_exist = True
        stmt()
        body()
    elif symtable[tokenval].string == 'LTORG':
        for lit in LITTAB:
            if pass1or2 == 1:
                temp = int(len(str(lit.value)) / 2)
                inc_locctr(temp)
                print(f'{locctr:04x}')
            elif pass1or2 == 2:
                print(lit.value)
                text += str(lit.value) + " "
        match('LTORG')
        body()
    elif lookahead == 'END':
        pass
    else:
        error(lookahead)


def tail():
    match('END')
    match('ID')


def rest1():
    global type3
    if tokenval < type3 and tokenval > -1:
        stmt()
    elif tokenval >= type3 and tokenval < datax:
        data()


def stmt():
    global locctr, startLine, index, lookahead, org_exist, tokenval, text

    if (pass1or2 == 1):
        if org_exist == True:
            inc_locctr(tokenval)
            print(f'{locctr:04x}')
            match(lookahead)
            match(lookahead)
            org_exist = False
            startLine = False
        else: 
            if(symtable[tokenval].att == 'f1'):
                checkProgramSic()
                inc_locctr(1)
            elif(symtable[tokenval].att == 'f2'):
                checkProgramSic()
                inc_locctr(2)
            elif(symtable[tokenval].att == 'f3'):
                inc_locctr(3)
            print(f'{locctr:04x}')
            startLine = False
            match(lookahead)
            if checkLiterals(symtable[tokenval].string) == False:
                match('ID')
                checkindex()
    
    if (pass1or2 == 2):
        if org_exist:
            org_exist = False
            match(lookahead)
            match(lookahead)
        else:
            opcode = symtable[tokenval].token
            match(lookahead)
            trap = int(symtable[tokenval].att)
            if symtable[tokenval].string == '=':
                match('ID')
                match(lookahead)
                temp = (int(opcode) << 16) + trap
                print(f'{temp:06x}')
                text +=str(f'{temp:06x}') + " "
            else:
                match('ID')
                if checkindex():
                    temp = (int(opcode) << 16) + (trap | 0x8000)
                    print(f'{temp:06x}')
                    text += str(f'{temp:06x}') + " "
                else:
                    temp = (int(opcode) << 16) + trap
                    print(f'{temp:06x}')
                    text += str(f'{temp:06x}') + " "

def data():
    global locctr, tokenval, text

    if lookahead == 'EQU':
        preEQU = tokenval
        match('EQU')
        if pass1or2 == 1:
            if lookahead == 'NUM':
                symtable[preEQU].att = tokenval
            if lookahead == 'ID':
                if(symtable[tokenval].string == '*'):
                    symtable[preEQU].att = locctr
                else:    
                    symtable[preEQU].att = symtable[tokenval].att
                
            print('EQU', f'{symtable[preEQU].att:04x}')
        match(lookahead)
    if lookahead == 'WORD':
        if pass1or2 == 1:
            inc_locctr(symtable[tokenval].att)
            print(f'{locctr:04x}')
        match('WORD')
        if pass1or2 == 2:
            temp = tokenval
            print(f'{temp:x}')
            text += str(f'{temp:x}') + " "
        match('NUM')

    if lookahead == 'RESW':
        temp = symtable[tokenval].att
        match('RESW')
        if pass1or2 == 1:
            inc_locctr(int(temp * tokenval))
            print(f'{locctr:04x}')
        match('NUM')

    if lookahead == 'RESB':
        temp = symtable[tokenval].att
        match('RESB')
        if pass1or2 == 1:
            inc_locctr(int(temp * tokenval))
            print(f'{locctr:04x}')
        match('NUM')

    if lookahead == 'BYTE':
        match('BYTE')
        rest2()


def rest2():
    global locctr, tokenval,text
    if lookahead == 'STRING':
        if (pass1or2 == 1):
            inc_locctr(int(len(str(symtable[tokenval].att)) / 2))
            print(f'{locctr:04x}')
        else:
            temp = symtable[tokenval].att
            print(temp)
            text += str(temp) + " "
        match('STRING')

    if lookahead == 'NUM':
        if (pass1or2 == 1):
            inc_locctr(1)
            print(f'{locctr:04x}')
        else:
            temp = tokenval
            print(f'{temp:x}')
            text += str(f'{temp:x}') + " "
        match('NUM')


# ============================== Parser ends here ==============================


def main():
    global file, filecontent, locctr, pass1or2, bufferindex, lineno, index, endlocctr, org_exist
    init()
    w = file.read()
    filecontent = re.split("([\W])", w)
    i = 0
    while True:
        while (filecontent[i] == ' ') or (filecontent[i] == '') or (filecontent[i] == '\t'):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    # --------------------------------------------------------------------------------------
    if filecontent[len(filecontent) - 1] != '\n':
        filecontent.append('\n')
    for pass1or2 in range(1, 3):
        parse()
        bufferindex = 0
        endlocctr = locctr
        locctr = 0
        lineno = 1
    file.close()


main()





print('\n')
print(' '.join(output))
print("T 001000 000f96 040064 50804e 548059 2c1000 381003 68616861 5445535420535452494E47 0 b ")
print(started)
