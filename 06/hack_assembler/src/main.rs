// Hack 組譯器：把 .asm 翻成 .hack
// 用法：cargo run -- Prog.asm   （輸出 Prog.hack）

mod code;
mod parser;
mod symbol_table;

use parser::Instruction;
use std::fs;
use std::path::Path;
use std::process;
use symbol_table::SymbolTable;

fn assemble(source: &str) -> Result<Vec<String>, String> {
    // 解析每一行，保留行號以便回報錯誤
    let mut instructions: Vec<(usize, Instruction)> = Vec::new();
    for (i, line) in source.lines().enumerate() {
        match parser::parse_line(line) {
            Ok(Some(ins)) => instructions.push((i + 1, ins)),
            Ok(None) => {}
            Err(e) => return Err(format!("第 {} 行：{}", i + 1, e)),
        }
    }

    // 第一次掃描：只處理標籤（標籤不算指令，不增加行號）
    let mut symbols = SymbolTable::new();
    let mut rom_address: u16 = 0;
    for (line_no, ins) in &instructions {
        match ins {
            Instruction::Label(name) => symbols
                .add_label(name, rom_address)
                .map_err(|e| format!("第 {} 行：{}", line_no, e))?,
            _ => rom_address += 1,
        }
    }

    // 第二次掃描：真正翻譯
    let mut output = Vec::new();
    for (line_no, ins) in &instructions {
        let result: Result<String, String> = match ins {
            Instruction::Label(_) => continue,
            Instruction::A(sym) => {
                let value = if sym.chars().next().unwrap().is_ascii_digit() {
                    match sym.parse::<u16>() {
                        Ok(v) if v <= 32767 => Ok(v),
                        _ => Err(format!("A 指令的數值超出範圍：\"{}\"", sym)),
                    }
                } else {
                    Ok(symbols.get_or_add_variable(sym))
                };
                value.map(|v| format!("{:016b}", v))
            }
            Instruction::C { dest, comp, jump } => (|| {
                Ok(format!("111{}{}{}", code::comp(comp)?, code::dest(dest)?, code::jump(jump)?))
            })(),
        };
        output.push(result.map_err(|e| format!("第 {} 行：{}", line_no, e))?);
    }
    Ok(output)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 2 {
        eprintln!("用法：{} <檔案.asm>", args[0]);
        process::exit(1);
    }
    let input_path = Path::new(&args[1]);
    if input_path.extension().and_then(|e| e.to_str()) != Some("asm") {
        eprintln!("錯誤：輸入檔必須是 .asm 檔");
        process::exit(1);
    }

    let source = fs::read_to_string(input_path).unwrap_or_else(|e| {
        eprintln!("無法讀取 {}：{}", input_path.display(), e);
        process::exit(1);
    });

    match assemble(&source) {
        Ok(lines) => {
            let output_path = input_path.with_extension("hack");
            let mut text = lines.join("\n");
            text.push('\n');
            if let Err(e) = fs::write(&output_path, text) {
                eprintln!("無法寫入 {}：{}", output_path.display(), e);
                process::exit(1);
            }
            println!("完成：{} -> {}", input_path.display(), output_path.display());
        }
        Err(e) => {
            eprintln!("組譯失敗，{}", e);
            process::exit(1);
        }
    }
}
