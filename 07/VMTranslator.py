"""nand2tetris 專案 7:VM 翻譯器(堆疊運算 + 記憶體存取)

用法:
    python VMTranslator.py <檔案.vm>

會在同一個資料夾產生同名的 .asm 檔,例如:
    python VMTranslator.py StackArithmetic/SimpleAdd/SimpleAdd.vm
    -> StackArithmetic/SimpleAdd/SimpleAdd.asm
"""

import os
import sys

# ---------------------------------------------------------------- 指令表

ARITHMETIC_BINARY = {"add", "sub", "and", "or"}
ARITHMETIC_UNARY = {"neg", "not"}
ARITHMETIC_COMPARE = {"eq", "gt", "lt"}
ARITHMETIC = ARITHMETIC_BINARY | ARITHMETIC_UNARY | ARITHMETIC_COMPARE

# 這四個記憶體段透過「基底暫存器 + 偏移量」存取
SEGMENT_BASE = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}
SEGMENTS = set(SEGMENT_BASE) | {"constant", "static", "pointer", "temp"}

TEMP_BASE = 5  # temp 段從 RAM[5] 開始,共 8 格(RAM[5]~RAM[12])


# ---------------------------------------------------------------- Parser

class VMSyntaxError(Exception):
    pass


class Parser:
    """逐行讀取 .vm 檔,去掉註解與空白,把每行切成 (指令, 參數...)。"""

    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.lines = f.read().splitlines()

    def commands(self):
        """產生 (行號, 原始文字, tokens)。"""
        for number, raw in enumerate(self.lines, start=1):
            text = raw.split("//", 1)[0].strip()
            if text:
                yield number, text, text.split()


# ---------------------------------------------------------------- CodeWriter

class CodeWriter:
    """把 VM 指令翻成 Hack 組合語言。"""

    def __init__(self):
        self.out = []
        self.file_name = ""   # static 變數的前綴,例如 StaticTest.3
        self.label_count = 0  # 比較指令需要唯一標籤

    def set_file_name(self, name):
        self.file_name = name

    def emit(self, *lines):
        self.out.extend(lines)

    # 把 D 暫存器的值 push 到堆疊
    def _push_d(self):
        self.emit("@SP", "A=M", "M=D", "@SP", "M=M+1")

    # 從堆疊 pop 到 D 暫存器
    def _pop_d(self):
        self.emit("@SP", "AM=M-1", "D=M")

    # ---------------------------------------------------------- 算術

    def write_arithmetic(self, command):
        if command in ARITHMETIC_BINARY:
            op = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}[command]
            # y 在堆疊頂端,x 在 y 下面;結果覆蓋 x 的位置
            self._pop_d()
            self.emit("A=A-1", "M=" + op)
        elif command in ARITHMETIC_UNARY:
            op = {"neg": "-M", "not": "!M"}[command]
            self.emit("@SP", "A=M-1", "M=" + op)
        else:
            self._write_compare(command)

    def _write_compare(self, command):
        # 注意:這裡用 x - y 的正負判斷大小,
        # 若 x、y 異號且差值超出 16 位元範圍會溢位(課程測試不會遇到)。
        jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
        n = self.label_count
        self.label_count += 1
        true_label = "CMP$TRUE." + str(n)
        end_label = "CMP$END." + str(n)
        self._pop_d()
        self.emit(
            "A=A-1",
            "D=M-D",            # D = x - y
            "@" + true_label,
            "D;" + jump,
            "@SP",
            "A=M-1",
            "M=0",              # false
            "@" + end_label,
            "0;JMP",
            "(" + true_label + ")",
            "@SP",
            "A=M-1",
            "M=-1",             # true
            "(" + end_label + ")",
        )

    # ---------------------------------------------------------- push / pop

    def write_push_pop(self, command, segment, index):
        if command == "push":
            self._write_push(segment, index)
        else:
            self._write_pop(segment, index)

    def _address_of(self, segment, index):
        """pointer / temp / static 的固定位址(符號或數字)。"""
        if segment == "pointer":
            return "THIS" if index == 0 else "THAT"
        if segment == "temp":
            return str(TEMP_BASE + index)
        return self.file_name + "." + str(index)  # static

    def _write_push(self, segment, index):
        if segment == "constant":
            self.emit("@" + str(index), "D=A")
        elif segment in SEGMENT_BASE:
            self.emit(
                "@" + str(index), "D=A",
                "@" + SEGMENT_BASE[segment], "A=D+M", "D=M",
            )
        else:
            self.emit("@" + self._address_of(segment, index), "D=M")
        self._push_d()

    def _write_pop(self, segment, index):
        if segment in SEGMENT_BASE:
            # 先算出目標位址存到 R13,因為 pop 會用到 D
            self.emit(
                "@" + str(index), "D=A",
                "@" + SEGMENT_BASE[segment], "D=D+M",
                "@R13", "M=D",
            )
            self._pop_d()
            self.emit("@R13", "A=M", "M=D")
        else:
            self._pop_d()
            self.emit("@" + self._address_of(segment, index), "M=D")

    # ---------------------------------------------------------- 輸出

    def text(self):
        return "\n".join(self.out) + "\n"


# ---------------------------------------------------------------- 主流程

def translate(path):
    parser = Parser(path)
    writer = CodeWriter()
    writer.set_file_name(os.path.splitext(os.path.basename(path))[0])

    for number, text, tokens in parser.commands():
        command = tokens[0]
        writer.emit("// " + text)

        if command in ARITHMETIC:
            if len(tokens) != 1:
                raise VMSyntaxError("第 %d 行:%s 不需要參數" % (number, command))
            writer.write_arithmetic(command)

        elif command in ("push", "pop"):
            if len(tokens) != 3:
                raise VMSyntaxError("第 %d 行:%s 需要 segment 與 index" % (number, command))
            segment = tokens[1]
            if segment not in SEGMENTS:
                raise VMSyntaxError("第 %d 行:未知的記憶體段 %s" % (number, segment))
            try:
                index = int(tokens[2])
            except ValueError:
                raise VMSyntaxError("第 %d 行:index 必須是整數" % number)
            if index < 0:
                raise VMSyntaxError("第 %d 行:index 不可為負" % number)
            if segment == "pointer" and index > 1:
                raise VMSyntaxError("第 %d 行:pointer 只能是 0 或 1" % number)
            if segment == "temp" and index > 7:
                raise VMSyntaxError("第 %d 行:temp 只能是 0 到 7" % number)
            if command == "pop" and segment == "constant":
                raise VMSyntaxError("第 %d 行:不能 pop 到 constant" % number)
            writer.write_push_pop(command, segment, index)

        else:
            raise VMSyntaxError("第 %d 行:未知的指令 %s" % (number, command))

    return writer.text()


def main(argv):
    if len(argv) != 2 or not argv[1].endswith(".vm"):
        print("用法:python VMTranslator.py <檔案.vm>")
        return 1
    source = argv[1]
    if not os.path.isfile(source):
        print("找不到檔案:" + source)
        return 1
    try:
        asm = translate(source)
    except VMSyntaxError as error:
        print("翻譯失敗:" + str(error))
        return 1
    target = os.path.splitext(source)[0] + ".asm"
    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(asm)
    print("已輸出 " + target)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
