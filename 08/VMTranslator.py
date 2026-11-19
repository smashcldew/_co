"""nand2tetris 專案 8:VM 翻譯器(含程式流程控制與函式呼叫)

用法:
    python VMTranslator.py <檔案.vm 或 資料夾> [--bootstrap | --no-bootstrap]

輸出位置:
    單一檔案  Foo.vm      -> Foo.asm(同資料夾)
    資料夾    Dir/        -> Dir/Dir.asm(合併資料夾內所有 .vm,Sys.vm 排最前面)

bootstrap 程式碼(SP=256,然後 call Sys.init 0)的預設行為:
    資料夾:加入    單一檔案:不加入
    可用 --bootstrap / --no-bootstrap 強制指定。

各測試的建議用法:
    ProgramFlow/*、SimpleFunction     單一檔案,不需 bootstrap
    NestedCall                        資料夾,要加 --no-bootstrap(測試腳本自己設定 RAM)
    FibonacciElement、StaticsTest     資料夾,需要 bootstrap(預設即是)
"""

import os
import sys

# ---------------------------------------------------------------- 指令表

ARITHMETIC_BINARY = {"add", "sub", "and", "or"}
ARITHMETIC_UNARY = {"neg", "not"}
ARITHMETIC_COMPARE = {"eq", "gt", "lt"}
ARITHMETIC = ARITHMETIC_BINARY | ARITHMETIC_UNARY | ARITHMETIC_COMPARE

SEGMENT_BASE = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}
SEGMENTS = set(SEGMENT_BASE) | {"constant", "static", "pointer", "temp"}

TEMP_BASE = 5


# ---------------------------------------------------------------- Parser

class VMSyntaxError(Exception):
    pass


class Parser:
    """逐行讀取 .vm 檔,去掉註解與空白,把每行切成 tokens。"""

    def __init__(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.lines = f.read().splitlines()

    def commands(self):
        for number, raw in enumerate(self.lines, start=1):
            text = raw.split("//", 1)[0].strip()
            if text:
                yield number, text, text.split()


# ---------------------------------------------------------------- CodeWriter

class CodeWriter:
    """把 VM 指令翻成 Hack 組合語言。"""

    def __init__(self):
        self.out = []
        self.file_name = ""      # static 變數前綴
        self.function_name = ""  # 目前所在函式,用來替 label 加範圍
        self.label_count = 0     # 比較指令的唯一標籤
        self.return_count = 0    # call 的返回標籤

    def set_file_name(self, name):
        self.file_name = name

    def emit(self, *lines):
        self.out.extend(lines)

    def _push_d(self):
        self.emit("@SP", "A=M", "M=D", "@SP", "M=M+1")

    def _pop_d(self):
        self.emit("@SP", "AM=M-1", "D=M")

    # ---------------------------------------------------------- bootstrap

    def write_bootstrap(self):
        self.emit("// bootstrap: SP = 256; call Sys.init 0")
        self.emit("@256", "D=A", "@SP", "M=D")
        self.function_name = "Bootstrap"
        self.write_call("Sys.init", 0)
        self.function_name = ""

    # ---------------------------------------------------------- 算術

    def write_arithmetic(self, command):
        if command in ARITHMETIC_BINARY:
            op = {"add": "D+M", "sub": "M-D", "and": "D&M", "or": "D|M"}[command]
            self._pop_d()
            self.emit("A=A-1", "M=" + op)
        elif command in ARITHMETIC_UNARY:
            op = {"neg": "-M", "not": "!M"}[command]
            self.emit("@SP", "A=M-1", "M=" + op)
        else:
            self._write_compare(command)

    def _write_compare(self, command):
        # 以 x - y 的正負判斷大小;異號且差值超出 16 位元時會溢位(課程測試不會遇到)。
        jump = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]
        n = self.label_count
        self.label_count += 1
        true_label = "CMP$TRUE." + str(n)
        end_label = "CMP$END." + str(n)
        self._pop_d()
        self.emit(
            "A=A-1",
            "D=M-D",
            "@" + true_label,
            "D;" + jump,
            "@SP",
            "A=M-1",
            "M=0",
            "@" + end_label,
            "0;JMP",
            "(" + true_label + ")",
            "@SP",
            "A=M-1",
            "M=-1",
            "(" + end_label + ")",
        )

    # ---------------------------------------------------------- push / pop

    def write_push_pop(self, command, segment, index):
        if command == "push":
            self._write_push(segment, index)
        else:
            self._write_pop(segment, index)

    def _address_of(self, segment, index):
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

    # ---------------------------------------------------------- 程式流程

    def _scoped(self, label):
        """label 加上所在函式當前綴:函式名$標籤。"""
        if self.function_name:
            return self.function_name + "$" + label
        return label

    def write_label(self, label):
        self.emit("(" + self._scoped(label) + ")")

    def write_goto(self, label):
        self.emit("@" + self._scoped(label), "0;JMP")

    def write_if(self, label):
        self._pop_d()
        self.emit("@" + self._scoped(label), "D;JNE")

    # ---------------------------------------------------------- 函式

    def write_function(self, name, n_locals):
        self.function_name = name
        self.emit("(" + name + ")")
        for _ in range(n_locals):  # 建立 n_locals 個初始值為 0 的 local
            self.emit("@SP", "A=M", "M=0", "@SP", "M=M+1")

    def write_call(self, name, n_args):
        ret = self.function_name + "$ret." + str(self.return_count)
        self.return_count += 1

        # push return-address
        self.emit("@" + ret, "D=A")
        self._push_d()
        # push LCL、ARG、THIS、THAT(保存呼叫者的環境)
        for reg in ("LCL", "ARG", "THIS", "THAT"):
            self.emit("@" + reg, "D=M")
            self._push_d()
        # ARG = SP - n_args - 5
        self.emit(
            "@SP", "D=M",
            "@" + str(n_args + 5), "D=D-A",
            "@ARG", "M=D",
        )
        # LCL = SP
        self.emit("@SP", "D=M", "@LCL", "M=D")
        # goto 被呼叫的函式
        self.emit("@" + name, "0;JMP")
        self.emit("(" + ret + ")")

    def write_return(self):
        self.emit(
            "@LCL", "D=M",
            "@R13", "M=D",             # R13 = FRAME = LCL
            "@5", "A=D-A", "D=M",
            "@R14", "M=D",             # R14 = RET = *(FRAME-5),要在覆蓋 *ARG 之前先存
        )
        self._pop_d()
        self.emit(
            "@ARG", "A=M", "M=D",      # *ARG = pop()(回傳值)
            "@ARG", "D=M+1",
            "@SP", "M=D",              # SP = ARG + 1
        )
        # 依序還原 THAT、THIS、ARG、LCL(FRAME-1 ... FRAME-4)
        for reg in ("THAT", "THIS", "ARG", "LCL"):
            self.emit("@R13", "AM=M-1", "D=M", "@" + reg, "M=D")
        self.emit("@R14", "A=M", "0;JMP")  # goto RET

    # ---------------------------------------------------------- 輸出

    def text(self):
        return "\n".join(self.out) + "\n"


# ---------------------------------------------------------------- 主流程

def _int_arg(number, token, what):
    try:
        value = int(token)
    except ValueError:
        raise VMSyntaxError("第 %d 行:%s 必須是整數" % (number, what))
    if value < 0:
        raise VMSyntaxError("第 %d 行:%s 不可為負" % (number, what))
    return value


def translate_file(path, writer):
    """翻譯單一 .vm 檔,結果累積在 writer。"""
    writer.set_file_name(os.path.splitext(os.path.basename(path))[0])

    for number, text, tokens in Parser(path).commands():
        command = tokens[0]
        writer.emit("// " + text)

        def need(count):
            if len(tokens) != count:
                raise VMSyntaxError(
                    "第 %d 行:%s 需要 %d 個參數" % (number, command, count - 1))

        if command in ARITHMETIC:
            need(1)
            writer.write_arithmetic(command)

        elif command in ("push", "pop"):
            need(3)
            segment = tokens[1]
            if segment not in SEGMENTS:
                raise VMSyntaxError("第 %d 行:未知的記憶體段 %s" % (number, segment))
            index = _int_arg(number, tokens[2], "index")
            if segment == "pointer" and index > 1:
                raise VMSyntaxError("第 %d 行:pointer 只能是 0 或 1" % number)
            if segment == "temp" and index > 7:
                raise VMSyntaxError("第 %d 行:temp 只能是 0 到 7" % number)
            if command == "pop" and segment == "constant":
                raise VMSyntaxError("第 %d 行:不能 pop 到 constant" % number)
            writer.write_push_pop(command, segment, index)

        elif command == "label":
            need(2)
            writer.write_label(tokens[1])
        elif command == "goto":
            need(2)
            writer.write_goto(tokens[1])
        elif command == "if-goto":
            need(2)
            writer.write_if(tokens[1])

        elif command == "function":
            need(3)
            writer.write_function(tokens[1], _int_arg(number, tokens[2], "區域變數數量"))
        elif command == "call":
            need(3)
            writer.write_call(tokens[1], _int_arg(number, tokens[2], "參數數量"))
        elif command == "return":
            need(1)
            writer.write_return()

        else:
            raise VMSyntaxError("第 %d 行:未知的指令 %s" % (number, command))

    writer.function_name = ""  # 離開這個檔案,函式範圍結束


def collect_sources(path):
    """回傳 (要翻譯的 .vm 清單, 輸出的 .asm 路徑, 是否為資料夾)。"""
    if os.path.isdir(path):
        folder = os.path.abspath(path)
        files = sorted(f for f in os.listdir(folder) if f.endswith(".vm"))
        if not files:
            raise VMSyntaxError("資料夾裡沒有 .vm 檔:" + path)
        if "Sys.vm" in files:  # Sys.vm 放最前面,沒有 bootstrap 時也會從它開始執行
            files.remove("Sys.vm")
            files.insert(0, "Sys.vm")
        sources = [os.path.join(folder, f) for f in files]
        target = os.path.join(folder, os.path.basename(folder) + ".asm")
        return sources, target, True
    if os.path.isfile(path) and path.endswith(".vm"):
        return [path], os.path.splitext(path)[0] + ".asm", False
    raise VMSyntaxError("請提供 .vm 檔或資料夾:" + path)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = [a for a in argv[1:] if a.startswith("--")]
    if len(args) != 1 or any(f not in ("--bootstrap", "--no-bootstrap") for f in flags):
        print("用法:python VMTranslator.py <檔案.vm 或 資料夾> [--bootstrap | --no-bootstrap]")
        return 1

    try:
        sources, target, is_folder = collect_sources(args[0])
        use_bootstrap = is_folder  # 預設:資料夾才加 bootstrap
        if "--bootstrap" in flags:
            use_bootstrap = True
        if "--no-bootstrap" in flags:
            use_bootstrap = False

        writer = CodeWriter()
        if use_bootstrap:
            writer.write_bootstrap()
        for source in sources:
            translate_file(source, writer)
    except VMSyntaxError as error:
        print("翻譯失敗:" + str(error))
        return 1

    with open(target, "w", encoding="utf-8", newline="\n") as f:
        f.write(writer.text())
    print("已輸出 " + target + (" (含 bootstrap)" if use_bootstrap else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
