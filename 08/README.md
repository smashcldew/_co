# 專案 8:VM 翻譯器(二)程式流程與函式呼叫

這是 [nand2tetris](https://www.nand2tetris.org/) 第 8 章的作業,承接專案 7。翻譯器在原有的算術與記憶體存取之外,新增了 **程式流程控制** 與 **函式呼叫**,並能把整個資料夾的多個 `.vm` 檔合併翻成一個 `.asm`。

```
Foo.vm 或 資料夾/  ──►  VMTranslator.py  ──►  .asm  ──►  CPU Emulator 執行
```

## 資料夾結構

```
08/
├── VMTranslator.py              翻譯器本體
├── ProgramFlow/
│   ├── BasicLoop/               測試:label / if-goto 迴圈
│   └── FibonacciSeries/         測試:流程控制 + 記憶體操作
└── FunctionCalls/
    ├── SimpleFunction/          測試:function 與 return
    ├── NestedCall/              測試:巢狀呼叫,保存與還原環境
    ├── FibonacciElement/        測試:遞迴 + bootstrap + 多檔
    └── StaticsTest/             測試:不同檔案的 static 變數互不干擾
```

每個測試資料夾內有 `.vm`(輸入)、`.tst`(CPU Emulator 腳本)、`.cmp`(預期輸出)。

## 使用方式

```
python VMTranslator.py <檔案.vm 或 資料夾> [--bootstrap | --no-bootstrap]
```

| 輸入 | 輸出 |
|---|---|
| 單一 `.vm` 檔 | 同名 `.asm`,放在 `.vm` 旁邊 |
| 資料夾 | `資料夾名.asm`,放在該資料夾內;所有 `.vm` 合併,`Sys.vm` 排最前面 |

### 各測試的指令

```
python VMTranslator.py ProgramFlow\BasicLoop\BasicLoop.vm
python VMTranslator.py ProgramFlow\FibonacciSeries\FibonacciSeries.vm
python VMTranslator.py FunctionCalls\SimpleFunction\SimpleFunction.vm
python VMTranslator.py FunctionCalls\NestedCall --no-bootstrap
python VMTranslator.py FunctionCalls\FibonacciElement
python VMTranslator.py FunctionCalls\StaticsTest
```

### bootstrap 旗標

bootstrap 是程式開頭的初始化碼:設定 `SP = 256`,再執行 `call Sys.init 0`。

- 輸入是資料夾:預設 **加入**。
- 輸入是單一檔案:預設 **不加入**。
- `--bootstrap` / `--no-bootstrap` 可強制指定。
- `NestedCall` 的測試腳本會自己設定 RAM,所以必須加 `--no-bootstrap`。

> 如果系統使用 `python3` 指令,請把上面的 `python` 換成 `python3`。

## 支援的指令

| 類型 | 指令 |
|---|---|
| 算術 / 邏輯 | `add` `sub` `neg` `and` `or` `not` `eq` `gt` `lt` |
| 記憶體存取 | `push 段 i`、`pop 段 i`(八種記憶體段,同專案 7) |
| 程式流程 | `label`、`goto`、`if-goto` |
| 函式 | `function 名稱 k`、`call 名稱 n`、`return` |

## 新增功能的翻譯原理

### 流程控制

- `label L` 翻成 `(函式名$L)`。標籤加上所在函式當前綴,不同函式可以使用相同的標籤名稱。
- `goto L` 翻成無條件跳躍。
- `if-goto L` 先 pop 堆疊頂端,不為 0 就跳躍。

### 函式呼叫框架

呼叫 `call g n` 之後,堆疊上會形成這個框架:

```
 ARG →  參數 0 … 參數 n-1
        返回位址         (FRAME-5)
        呼叫者的 LCL     (FRAME-4)
        呼叫者的 ARG     (FRAME-3)
        呼叫者的 THIS    (FRAME-2)
        呼叫者的 THAT    (FRAME-1)
 LCL →  local 0 … local k-1(初始化為 0)
 SP  →  工作堆疊
```

### `call 名稱 n`

1. push 返回位址標籤
2. push `LCL`、`ARG`、`THIS`、`THAT`
3. `ARG = SP - n - 5`
4. `LCL = SP`
5. 跳到被呼叫的函式,並在後面放返回標籤

返回標籤命名為 `函式名$ret.編號`,每次呼叫都不同。

### `function 名稱 k`

放上函式入口標籤,並 push k 個 0 當作 local 變數。

### `return`

1. `FRAME = LCL`
2. `RET = *(FRAME-5)`(**必須先存**,否則無參數函式的回傳值會蓋掉返回位址)
3. `*ARG = pop()`,把回傳值放到呼叫者期待的位置
4. `SP = ARG + 1`
5. 依序還原 `THAT`、`THIS`、`ARG`、`LCL`
6. 跳到 `RET`

### 多檔案與 static

翻譯資料夾時,每個 `.vm` 檔的 static 變數會用該檔名當前綴(例如 `Class1.0`、`Class2.0`),所以不同檔案的 static 互不干擾。這正是 `StaticsTest` 要驗證的事。

## 程式結構

- **Parser**:讀入 `.vm`,去除註解與空白行,切成指令與參數。
- **CodeWriter**:輸出各類指令對應的 Hack 組合語言,並管理目前所在函式、返回標籤與比較標籤的編號。
- **translate_file / collect_sources / main**:處理單檔與資料夾、決定是否加入 bootstrap、檢查語法錯誤並回報行號。

輸出的 `.asm` 會保留每條 VM 指令作為註解,方便對照閱讀。

## 已知限制

比較指令用 `x - y` 的正負判斷大小。若 x、y 異號且差值超出 16 位元範圍,會發生溢位而判斷錯誤。課程提供的測試不會遇到這種情況。

## 測試結果

`BasicLoop`、`FibonacciSeries`、`SimpleFunction`、`NestedCall`、`FibonacciElement`、`StaticsTest` 在簡易 Hack 模擬器上,輸出皆與 `.cmp` 一致。這支翻譯器同時也通過專案 7 的五個測試。正式驗證請以官方 CPU Emulator 為準。
