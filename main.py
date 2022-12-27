# Template by Bruce A. Maxwell, 2015
#
# implements a simple assembler for the following assembly language
# 
# - One instruction or label per line.
#
# - Blank lines are ignored.
#
# - Comments start with a # as the first character and all subsequent
# - characters on the line are ignored.
#
# - Spaces delimit instruction elements.
#
# - A label ends with a colon and must be a single symbol on its own line.
#
# - A label can be any single continuous sequence of printable
# - characters; a colon or space terminates the symbol.
#
# - All immediate and address values are given in decimal.
#
# - Address values must be positive
#
# - Negative immediate values must have a preceeding '-' with no space
# - between it and the number.
#

# Language definition:
#
# LOAD D A   - load from address A to destination D
# LOADA D A  - load using the address register from address A + RE to destination D
# STORE S A  - store value in S to address A
# STOREA S A - store using the address register the value in S to address A + RE
# BRA L      - branch to label A
# BRAZ L     - branch to label A if the CR zero flag is set
# BRAN L     - branch to label L if the CR negative flag is set
# BRAO L     - branch to label L if the CR overflow flag is set
# BRAC L     - branch to label L if the CR carry flag is set
# CALL L     - call the routine at label L
# RETURN     - return from a routine
# HALT       - execute the halt/exit instruction
# PUSH S     - push source value S to the stack
# POP D      - pop form the stack and put in destination D
# OPORT S    - output to the global port from source S
# IPORT D    - input from the global port to destination D
# ADD A B C  - execute C <= A + B
# SUB A B C  - execute C <= A - B
# AND A B C  - execute C <= A and B  bitwise
# OR  A B C  - execute C <= A or B   bitwise
# XOR A B C  - execute C <= A xor B  bitwise
# SHIFTL A C - execute C <= A shift left by 1
# SHIFTR A C - execute C <= A shift right by 1
# ROTL A C   - execute C <= A rotate left by 1
# ROTR A C   - execute C <= A rotate right by 1
# MOVE A C   - execute C <= A where A is a source register
# MOVEI V C  - execute C <= value V
#

# 2-pass assembler
# pass 1: read through the instructions and put numbers on each instruction location
#         calculate the label values
#
# pass 2: read through the instructions and build the machine instructions
#

import sys
from enum import Enum


class SubCommandType(Enum):
    SUB_COMMAND_TYPE = 1
    ARGUMENT = 2
    LABEL = 3
    APPEND = 4  # appending bits


def format_sub_command(command, argument, current_argument):
    return command.subcommands[current_argument][argument.upper()]


def format_argument(command, argument, line_num):
    return dec2comp8(int(argument), line_num)


def format_label(command, argument, label):
    return ("{0:0" + str(command.label) + "b}").format(label[argument])


class Command:
    def __init__(self, opcode):
        self.subcommands = []
        self.argument = 0
        self.opcode = opcode
        self.label = 0
        self.order = []
        self.appended_bits = []

    def add_sub_command(self, op_dict):
        self.subcommands.append(op_dict)
        self.order.append(SubCommandType.SUB_COMMAND_TYPE)
        return self

    def add_argument(self, length: int):
        self.argument = length
        self.order.append(SubCommandType.ARGUMENT)
        return self

    def get_arguments(self):
        return self.argument

    def get_sub_commands(self):
        return self.subcommands

    def add_label(self, length: int):
        self.label = length
        self.order.append(SubCommandType.LABEL)
        return self

    def append_bits(self, length: int):
        self.appended_bits.append(length)
        self.order.append(SubCommandType.APPEND)
        return self

    def format(self, args, labels):  # make sure the first args is the first argument and not the command itself
        result = self.opcode
        current_indices = 0
        current_sub_command = 0
        current_append = 0
        for command_type in self.order:
            match command_type:
                case SubCommandType.APPEND:
                    result += '0' * self.appended_bits[current_append]
                    current_append += 1
                    continue
                case SubCommandType.SUB_COMMAND_TYPE:  # SUB_COMMAND_TYPE
                    result += format_sub_command(self, args[current_indices], current_sub_command)
                case SubCommandType.ARGUMENT:  # ARGUMENT
                    result += format_argument(self, args[current_indices], current_indices)
                case SubCommandType.LABEL:  # LABEL
                    result += str(format_label(self, args[current_indices], labels))
                case _:
                    pass
            current_indices += 1
        return result


__TABLE_B__ = {
    "RA": "000",
    "RB": "001",
    "RC": "010",
    "RD": "011",
    "RE": "100",
    "SP": "101"
}

__TABLE_C__ = {
    "RA": "000",
    "RB": "001",
    "RC": "010",
    "RD": "011",
    "RE": "100",
    "SP": "101",
    "PC": "110",
    "CR": "111"
}

__TABLE_D__ = {
    "RA": "000",
    "RB": "001",
    "RC": "010",
    "RD": "011",
    "RE": "100",
    "SP": "101",
    "PC": "110",
    "IR": "111"
}

__TABLE_E__ = {
    "RA": "000",
    "RB": "001",
    "RC": "010",
    "RD": "011",
    "RE": "100",
    "SP": "101",
    "ZEROS": "110",
    "ONES": "111"
}

__LOAD__ = Command("00000").add_sub_command(__TABLE_B__).add_argument(8)
# notice an extra 0 or 1 at the end of the load
# due to LOAD not wanting to move register E
__LOAD_A__ = Command("00001").add_sub_command(__TABLE_B__).add_argument(8)
__STORE__ = Command("00010").add_sub_command(__TABLE_B__).add_argument(8)
__STORE_A__ = Command("00011").add_sub_command(__TABLE_B__).add_argument(8)
__BRA__ = Command("00100000").add_label(8)
__BRA_Z__ = Command("00110000").add_label(8)
__BRA_N__ = Command("00110010").add_label(8)
__BRA_O__ = Command("00110001").add_label(8)
__BRA_C__ = Command("00110011").add_label(8)
__CALL__ = Command("00110100").add_label(8)
__RETURN__ = Command("001110000000000")
__HALT__ = Command("0011110000000000")
__PUSH__ = Command("0100").add_sub_command(__TABLE_C__)
__POP__ = Command("0101").add_sub_command(__TABLE_C__)
__O_PORT__ = Command("0110").add_sub_command(__TABLE_D__)
__I_PORT__ = Command("0111").add_sub_command(__TABLE_B__)
__ADD__ = Command("1000").add_sub_command(__TABLE_E__).add_sub_command(__TABLE_B__).append_bits(3) \
    .add_sub_command(__TABLE_E__)
__SUB__ = Command("1001").add_sub_command(__TABLE_E__).add_sub_command(__TABLE_B__).append_bits(3) \
    .add_sub_command(__TABLE_E__)
__AND__ = Command("1010").add_sub_command(__TABLE_E__).add_sub_command(__TABLE_B__).append_bits(3) \
    .add_sub_command(__TABLE_E__)
__OR__ = Command("1011").add_sub_command(__TABLE_E__).add_sub_command(__TABLE_B__).append_bits(3) \
    .add_sub_command(__TABLE_E__)
__XOR__ = Command("1100").add_sub_command(__TABLE_E__).add_sub_command(__TABLE_B__).append_bits(3) \
    .add_sub_command(__TABLE_E__)
__SHIFT_L__ = Command("11010").add_sub_command(__TABLE_E__).append_bits(5).add_sub_command(
    __TABLE_B__)  # I'm using the sub command to auto add appended bits inbetween two bits
__SHIFT_R__ = Command("11011").add_sub_command(__TABLE_E__).append_bits(5).add_sub_command(
    __TABLE_B__)
__ROT_L__ = Command("11100").add_sub_command(__TABLE_E__).append_bits(5).add_sub_command(
    __TABLE_B__)
__ROT_R__ = Command("11101").add_sub_command(__TABLE_E__).append_bits(5).add_sub_command(
    __TABLE_B__)
__MOVE__ = Command("11110").add_sub_command(__TABLE_D__).append_bits(5).add_sub_command(__TABLE_B__)
__MOVE_I__ = Command("11111").add_argument(8).add_sub_command(__TABLE_B__)

__COMMAND_DICTIONARY__ = {
    "LOAD": __LOAD__,
    "LOADA": __LOAD_A__,
    "STORE": __STORE__,
    "STOREA": __STORE_A__,
    "BRA": __BRA__,
    "BRAZ": __BRA_Z__,
    "BRAN": __BRA_N__,
    "BRAO": __BRA_O__,
    "BRAC": __BRA_C__,
    "CALL": __CALL__,
    "RETURN": __RETURN__,
    "HALT": __HALT__,
    "PUSH": __PUSH__,
    "POP": __POP__,
    "OPORT": __O_PORT__,
    "IPORT": __I_PORT__,
    "ADD": __ADD__,
    "SUB": __SUB__,
    "AND": __AND__,
    "OR": __OR__,
    "XOR": __XOR__,
    "SHIFTL": __SHIFT_L__,
    "SHIFTR": __SHIFT_R__,
    "ROTL": __ROT_L__,
    "ROTR": __ROT_R__,
    "MOVE": __MOVE__,
    "MOVEI": __MOVE_I__
}


# converts d to an 8-bit 2-s complement binary value
def dec2comp8(d, linenum):
    try:
        if d > 0:
            l = d.bit_length()
            v = "00000000"
            v = v[0:8 - l] + format(d, 'b')
        elif d < 0:
            dt = 128 + d
            l = dt.bit_length()
            v = "10000000"
            v = v[0:8 - l] + format(dt, 'b')[:]
        else:
            v = "00000000"
    except:
        print
        'Invalid decimal number on line %d' % (linenum)
        exit()

    return v


# converts d to an 8-bit unsigned binary value
def dec2bin8(d, linenum):
    if d > 0:
        l = d.bit_length()
        v = "00000000"
        v = v[0:8 - l] + format(d, 'b')
    elif d == 0:
        v = "00000000"
    else:
        print
        'Invalid address on line %d: value is negative' % (linenum)
        exit()

    return v


# Tokenizes the input data, discarding white space and comments
# returns the tokens as a list of lists, one list for each line.
#
# The tokenizer also converts each character to lower case.
def tokenize(fp):
    tokens = []

    # start of the file
    fp.seek(0)

    lines = fp.readlines()

    # strip white space and comments from each line
    for line in lines:
        ls = line.strip()
        uls = ''
        for c in ls:
            if c != '#':
                uls = uls + c
            else:
                break

        # skip blank lines
        if len(uls) == 0:
            continue

        # split on white space
        words = uls.split()

        newwords = []
        for word in words:
            newwords.append(word.lower())

        tokens.append(newwords)

    return tokens


# reads through the file and returns a dictionary of all location
# labels with their line numbers
def pass1(tokens):
    line_number = 0
    dictionary = {}
    for label in tokens:
        if label[0].endswith(":"):  # check to see if the line is formatted as a label
            dictionary[label[0].replace(":", "")] = line_number  # add it to a dictionary
            tokens.remove(label)  # remove the label
        line_number += 1  # change current line number

    return dictionary


def pass2(tokens, labels, __instruction_size__=16):
    argument_code = []
    current_argument = 0
    for line in tokens:
        if not (line[0].upper() in __COMMAND_DICTIONARY__):
            continue
        command = __COMMAND_DICTIONARY__.get(line[0].upper())
        line.pop(0)
        argument_code.append("{:02x}".format(current_argument) + " : " + (command.format(line, labels))
                             .ljust(__instruction_size__, '0'))  # add
        # formatted command

        current_argument += 1
    if not current_argument == 256:
        argument_code.append('[' + '{:02x}'.format(current_argument) + '..FF] : 11111111111111111')
    return argument_code


def main(argv):
    if len(argv) < 2:
        print
        'Usage: python %s <filename>' % (argv[0])
        exit()
    # open() is the python3 version of file()
    fp = open(argv[1], 'rU')

    tokens = tokenize(fp)

    labels = pass1(tokens)

    print(tokens)

    argument_code = pass2(tokens, labels)

    print(*argument_code, sep="\n")

    f = open(argv[1].split(".")[0] + ".mif", "w")  # remove the .txt and add the .mif

    # build the file
    f.write("DEPTH = 256;\n")
    f.write("WIDTH = 16;\n")
    f.write("ADDRESS_RADIX = HEX;\n")
    f.write("DATA_RADIX = BIN;\n")
    f.write("CONTENT\n")
    f.write("BEGIN\n")
    for instruction in argument_code:
        f.write(instruction + ";\n")
    f.write("END")

    f.close()
    fp.close()

    # execute pass1 and pass2 then print it out as an MIF file

    return


if __name__ == "__main__":
    main(sys.argv)
