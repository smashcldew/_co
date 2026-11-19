# 專案 7:VM 翻譯器(一)堆疊運算與記憶體存取

這是 [nand2tetris](https://www.nand2tetris.org/) 第 7 章的作業。目標是寫一個 **VM 翻譯器**:把高階的虛擬機器指令(`.vm`)翻譯成 Hack 電腦能執行的組合語言(`.asm`)。

```
Foo.vm  ──►  VMTranslator.py  ──►  Foo.asm  ──►  CPU Emulator 執行
```

本專案用 Python 實作,只處理本章要求的兩類指令:算術運算,以及 `push` / `pop`。

## 資料夾結構

```
07/
├── VMTranslator.py          翻譯器本體
├── StackArithmetic/
│   ├── SimpleAdd/           測試:基本加法
│   └── StackTest/           測試:所有算術與比較指令
└── MemoryAccess/
    ├── BasicTest/           測試:local / argument / this / that / temp
    ├── PointerTest/         測試:pointer
    └── StaticTest/          測試:static
```

每個測試資料夾內有 `.vm`(輸入)、`.tst`(CPU Emulator 測試腳本)、`.cmp`(預期輸出)。

## 使用方式

```
python VMTranslator.py <檔案.vm>
```

例如:

```
python VMTranslator.py StackArithmetic\SimpleAdd\SimpleAdd.vm
```

會在 `.vm` 檔旁邊產生同名的 `.asm`。接著在官方 CPU Emulator 載入對應的 `.tst`,就會執行並與 `.cmp` 比對。

> 如果系統使用 `python3` 指令,請把上面的 `python` 換成 `python3`。

## 支援的指令

| 類型 | 指令 |
|---|---|
| 算術 / 邏輯 | `add` `sub` `neg` `and` `or` `not` |
| 比較 | `eq` `gt` `lt` |
| 記憶體存取 | `push 段 i`、`pop 段 i` |

記憶體段共八種:`constant`、`local`、`argument`、`this`、`that`、`temp`、`pointer`、`static`。

## 翻譯原理

### 堆疊與暫存器

Hack 的 RAM 配置如下,翻譯器依此產生程式碼:

| 位址 | 名稱 | 用途 |
|---|---|---|
| RAM[0] | SP | 堆疊指標,指向下一個空位 |
| RAM[1] | LCL | local 段的基底位址 |
| RAM[2] | ARG | argument 段的基底位址 |
| RAM[3] | THIS | this 段的基底位址 |
| RAM[4] | THAT | that 段的基底位址 |
| RAM[5–12] | temp | temp 段(8 格) |
| RAM[13–15] | R13–R15 | 翻譯器自用的暫存空間 |
| RAM[16–255] | static | 靜態變數 |
| RAM[256–2047] | stack | 堆疊 |

### 各類指令怎麼翻

- **二元運算**(`add`、`sub`、`and`、`or`):pop 出 y,直接對堆疊上的 x 運算,結果留在 x 的位置。
- **一元運算**(`neg`、`not`):直接修改堆疊頂端的值。
- **比較**(`eq`、`gt`、`lt`):計算 `x - y`,依結果跳到「真」或「假」的標籤,寫入 `-1`(true)或 `0`(false)。每次比較都會產生唯一的標籤。
- **`push constant i`**:把常數 i 放進 D,再壓入堆疊。
- **`local` / `argument` / `this` / `that`**:位址 = 基底暫存器 + i。`pop` 時先把算出的位址存到 R13,避免與 D 暫存器衝突。
- **`temp i`**:固定位址 `5 + i`。
- **`pointer 0/1`**:對應 `THIS` / `THAT`。
- **`static i`**:翻成符號 `檔名.i`,由組譯器自動配置位址,所以不同檔案的 static 互不干擾。

輸出的 `.asm` 會保留每條 VM 指令作為註解(例如 `// push constant 7`),方便對照閱讀。

## 程式結構

`VMTranslator.py` 分成三個部分:

- **Parser**:讀入 `.vm`,去除註解與空白行,把每行切成指令與參數。
- **CodeWriter**:依指令類型輸出對應的 Hack 組合語言。
- **translate / main**:串接兩者,檢查語法錯誤(未知指令、參數數量不對、`pointer` 超出範圍等)並回報行號。

## 已知限制

比較指令用 `x - y` 的正負判斷大小。若 x、y 異號且差值超出 16 位元範圍,會發生溢位而判斷錯誤。課程提供的測試不會遇到這種情況。

## 測試結果

五個測試(`SimpleAdd`、`StackTest`、`BasicTest`、`PointerTest`、`StaticTest`)在簡易 Hack 模擬器上,輸出皆與 `.cmp` 一致。正式驗證請以官方 CPU Emulator 為準。
