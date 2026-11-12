// Parser 模組：清理每一行並判斷指令類型、拆出欄位

#[derive(Debug, PartialEq)]
pub enum Instruction {
    A(String),                                          // @xxx，存 xxx
    C { dest: String, comp: String, jump: String },     // dest=comp;jump
    Label(String),                                      // (XXX)，存 XXX
}

/// 去掉 // 之後的註解，並移除所有空白
pub fn clean_line(line: &str) -> String {
    let no_comment = line.split("//").next().unwrap_or("");
    no_comment.chars().filter(|c| !c.is_whitespace()).collect()
}

/// 解析一行。空行或純註解回傳 Ok(None)
pub fn parse_line(line: &str) -> Result<Option<Instruction>, String> {
    let s = clean_line(line);
    if s.is_empty() {
        return Ok(None);
    }

    if let Some(rest) = s.strip_prefix('@') {
        if rest.is_empty() {
            return Err("@ 後面沒有內容".to_string());
        }
        return Ok(Some(Instruction::A(rest.to_string())));
    }

    if s.starts_with('(') {
        if !s.ends_with(')') || s.len() < 3 {
            return Err(format!("標籤格式錯誤：\"{}\"", s));
        }
        return Ok(Some(Instruction::Label(s[1..s.len() - 1].to_string())));
    }

    // C 指令：先用 ; 分出 jump，再用 = 分出 dest 與 comp
    let (left, jump) = match s.split_once(';') {
        Some((l, j)) => (l, j),
        None => (s.as_str(), ""),
    };
    let (dest, comp) = match left.split_once('=') {
        Some((d, c)) => (d, c),
        None => ("", left),
    };
    if comp.is_empty() {
        return Err(format!("缺少 comp：\"{}\"", s));
    }
    Ok(Some(Instruction::C {
        dest: dest.to_string(),
        comp: comp.to_string(),
        jump: jump.to_string(),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_blank_and_comment() {
        assert_eq!(parse_line("   ").unwrap(), None);
        assert_eq!(parse_line("// hello").unwrap(), None);
    }

    #[test]
    fn test_a_and_label() {
        assert_eq!(parse_line("  @100 // x").unwrap(), Some(Instruction::A("100".into())));
        assert_eq!(parse_line("(LOOP)").unwrap(), Some(Instruction::Label("LOOP".into())));
    }

    #[test]
    fn test_c() {
        assert_eq!(
            parse_line("D=M;JGT").unwrap(),
            Some(Instruction::C { dest: "D".into(), comp: "M".into(), jump: "JGT".into() })
        );
        assert_eq!(
            parse_line("0;JMP").unwrap(),
            Some(Instruction::C { dest: "".into(), comp: "0".into(), jump: "JMP".into() })
        );
        assert_eq!(
            parse_line("M = D + 1").unwrap(),
            Some(Instruction::C { dest: "M".into(), comp: "D+1".into(), jump: "".into() })
        );
    }
}
