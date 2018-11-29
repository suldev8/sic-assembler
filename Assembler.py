import re
import instfile


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []


# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))


def lookup(s):
    for i in range(0, symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1


def insert(s, t, a):
    symtable.append(Entry(s, t, a))
    return symtable.__len__() - 1



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


# ============================== Parser starts here ==============================
def parse():
    sic()


def sic():
    global lookahead
    header()
    body()
    tail()


def header():
    global lookahead, locctr, tokenval, output, endlocctr
    lookahead = lexan()
    program = tokenval

    match('ID')
    match('START')
    locctr += tokenval

    if pass1or2 == 1:
        print('Pass 1:')
        print(hex(locctr))
    else:
        output.append('H')
        output.append(symtable[program].string)
        output.append(hex(locctr))
        output.append(hex(endlocctr - locctr))
        output.append('\n')
        #print(' '.join(output))
        
        print('\nPass 2:')

    match('NUM')


def body():
    global type3, org_exist

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
    global locctr, startLine, index, lookahead, org_exist, tokenval


    if (pass1or2 == 1):
        if org_exist == True:
            match(lookahead)
            locctr = tokenval
            print(hex(locctr))
            match(lookahead)
            org_exist = False
            startLine = False
        else:
            locctr += symtable[tokenval].att
            print(hex(locctr))
            startLine = False
            match(lookahead)
            match('ID')
            checkindex()
    if (pass1or2 == 2):
        if org_exist == True:
            org_exist = False
            match(lookahead)
            match(lookahead)
        else:
            opcode = symtable[tokenval].token
            match(lookahead)
            trap = int(symtable[tokenval].att)
            match('ID')
            
            if checkindex():
                temp = hex((int(opcode) << 16) + (trap | 0x8000))
                print(temp)
            else:
                temp = hex((int(opcode) << 16) + trap)
                print(temp)

def data():
    global locctr, tokenval
    
    #if lookahead == 'EQU':
     #   if pass1or2 == 1:
      #      locctr 
    if lookahead == 'WORD':
        if pass1or2 == 1:
            locctr += symtable[tokenval].att
            print(hex(locctr))
        match('WORD')
        if pass1or2 == 2:
            temp = hex(tokenval)
            print(temp)
        match('NUM')

    if lookahead == 'RESW':
        temp = symtable[tokenval].att
        match('RESW')
        if pass1or2 == 1:
            locctr += int(temp * tokenval)
            print(hex(locctr))
        match('NUM')

    if lookahead == 'RESB':
        temp = symtable[tokenval].att
        match('RESB')
        if pass1or2 == 1:
            locctr += int(temp * tokenval)
            print(hex(locctr))
        match('NUM')

    if lookahead == 'BYTE':
        match('BYTE')
        rest2()


def rest2():
    global locctr, tokenval
    if lookahead == 'STRING':
        if (pass1or2 == 1):
            locctr += int(len(str(symtable[tokenval].att)) / 2)
            print(hex(locctr))
        else:
            temp = "0x" + symtable[tokenval].att
            print(temp)
        match('STRING')

    if lookahead == 'NUM':
        if (pass1or2 == 1):
            locctr += 1
            print(hex(locctr))
        else:
            temp = hex(tokenval)
            print(temp)
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