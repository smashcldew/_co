// Code 模組：把 dest / comp / jump 的助憶符轉成二進位字串

/// dest -> 3 位元（順序為 A D M）
pub fn dest(mnemonic: &str) -> Result<String, String> {
    let mut bits = [b'0'; 3];
    for c in mnemonic.chars() {
        match c {
            'A' => bits[0] = b'1',
            'D' => bits[1] = b'1',
            'M' => bits[2] = b'1',
            _ => return Err(format!("未知的 dest：\"{}\"", mnemonic)),
        }
    }
    Ok(String::from_utf8(bits.to_vec()).unwrap())
}

/// comp -> 7 位元（a 位元 + c1~c6）
pub fn comp(mnemonic: &str) -> Result<String, String> {
    // 含 M 代表 a = 1；把 M 換成 A 後，查同一張表
    let (a, name) = if mnemonic.contains('M') {
        ("1", mnemonic.replace('M', "A"))
    } else {
        ("0", mnemonic.to_string())
    };
    let c = match name.as_str() {
        "0" => "101010",
        "1" => "111111",
        "-1" => "111010",
        "D" => "001100",
        "A" => "110000",
        "!D" => "001101",
        "!A" => "110001",
        "-D" => "001111",
        "-A" => "110011",
        "D+1" => "011111",
        "A+1" => "110111",
        "D-1" => "001110",
        "A-1" => "110010",
        "D+A" | "A+D" => "000010",
        "D-A" => "010011",
        "A-D" => "000111",
        "D&A" | "A&D" => "000000",
        "D|A" | "A|D" => "010101",
        _ => return Err(format!("未知的 comp：\"{}\"", mnemonic)),
    };
    Ok(format!("{}{}", a, c))
}

/// jump -> 3 位元
pub fn jump(mnemonic: &str) -> Result<&'static str, String> {
    Ok(match mnemonic {
        "" => "000",
        "JGT" => "001",
        "JEQ" => "010",
        "JGE" => "011",
        "JLT" => "100",
        "JNE" => "101",
        "JLE" => "110",
        "JMP" => "111",
        _ => return Err(format!("未知的 jump：\"{}\"", mnemonic)),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dest() {
        assert_eq!(dest("").unwrap(), "000");
        assert_eq!(dest("M").unwrap(), "001");
        assert_eq!(dest("D").unwrap(), "010");
        assert_eq!(dest("AM").unwrap(), "101");
        assert_eq!(dest("AMD").unwrap(), "111");
        assert!(dest("X").is_err());
    }

    #[test]
    fn test_comp() {
        assert_eq!(comp("0").unwrap(), "0101010");
        assert_eq!(comp("D+1").unwrap(), "0011111");
        assert_eq!(comp("M").unwrap(), "1110000");
        assert_eq!(comp("D+M").unwrap(), "1000010");
        assert_eq!(comp("D-M").unwrap(), "1010011");
        assert!(comp("D*A").is_err());
    }

    #[test]
    fn test_jump() {
        assert_eq!(jump("").unwrap(), "000");
        assert_eq!(jump("JMP").unwrap(), "111");
        assert!(jump("JXX").is_err());
    }
}
