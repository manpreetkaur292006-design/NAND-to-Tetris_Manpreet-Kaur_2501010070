import re
import sys

SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")
DIGITS_RE = re.compile(r"^[0-9]+$")

COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101", "!A": "0110001",
    "-D": "0001111", "-A": "0110011", "D+1": "0011111", "A+1": "0110111",
    "D-1": "0001110", "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111",
    "M-1": "1110010", "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}

DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}

JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}


def predefined_symbols():
    table = {
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 16384, "KBD": 24576,
    }
    for i in range(16):
        table["R" + str(i)] = i
    return table


def clean(line):
    line = line.split("//")[0]
    return "".join(line.split())


def first_pass(lines, symbols, errors):
    instructions = []
    for number, raw in enumerate(lines, start=1):
        code = clean(raw)
        if code == "":
            continue
        if code.startswith("("):
            if not code.endswith(")") or len(code) < 3:
                errors.append(f"Line {number}: invalid label '{code}'")
                continue
            name = code[1:-1]
            if not SYMBOL_RE.match(name):
                errors.append(f"Line {number}: invalid label name '{name}'")
                continue
            if name in symbols:
                errors.append(f"Line {number}: label '{name}' is already defined")
                continue
            symbols[name] = len(instructions)
            continue
        instructions.append((number, code))
    return instructions


def translate_a(number, code, symbols, state, errors):
    text = code[1:]
    if text == "":
        errors.append(f"Line {number}: '@' must be followed by a number or a symbol")
        return None
    if DIGITS_RE.match(text):
        value = int(text)
        if value > 32767:
            errors.append(f"Line {number}: address {value} is too large (maximum is 32767)")
            return None
    elif SYMBOL_RE.match(text):
        if text not in symbols:
            symbols[text] = state["next_var"]
            state["next_var"] += 1
        value = symbols[text]
    else:
        errors.append(f"Line {number}: invalid A-instruction '{code}'")
        return None
    return "0" + format(value, "015b")


def translate_c(number, code, errors):
    if "=" in code:
        dest, rest = code.split("=", 1)
    else:
        dest, rest = "", code
    if ";" in rest:
        comp, jump = rest.split(";", 1)
    else:
        comp, jump = rest, ""

    if dest not in DEST:
        errors.append(f"Line {number}: invalid destination '{dest}' in '{code}'")
        return None
    if comp not in COMP:
        errors.append(f"Line {number}: invalid computation '{comp}' in '{code}'")
        return None
    if jump not in JUMP:
        errors.append(f"Line {number}: invalid jump '{jump}' in '{code}'")
        return None
    return "111" + COMP[comp] + DEST[dest] + JUMP[jump]


def second_pass(instructions, symbols, errors):
    state = {"next_var": 16}
    output = []
    for number, code in instructions:
        if code.startswith("@"):
            binary = translate_a(number, code, symbols, state, errors)
        else:
            binary = translate_c(number, code, errors)
        if binary is not None:
            output.append(binary)
    return output


def assemble(path):
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print(f"Error: cannot find file '{path}'")
        return False

    errors = []
    symbols = predefined_symbols()
    instructions = first_pass(lines, symbols, errors)
    output = second_pass(instructions, symbols, errors)

    if errors:
        errors.sort(key=lambda e: int(e.split(":")[0].split()[1]))
        for message in errors:
            print(message)
        print(f"Assembly failed with {len(errors)} error(s). No .hack file was written.")
        return False

    if path.lower().endswith(".asm"):
        out_path = path[:-4] + ".hack"
    else:
        out_path = path + ".hack"
    with open(out_path, "w") as f:
        f.write("\n".join(output) + "\n")
    print(f"Done: {len(output)} instructions written to {out_path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assembler.py <file.asm>")
        sys.exit(1)
    if not assemble(sys.argv[1]):
        sys.exit(1)