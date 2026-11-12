// SymbolTable 模組：符號與位址的對應表
use std::collections::HashMap;

pub struct SymbolTable {
    table: HashMap<String, u16>,
    next_var: u16, // 下一個變數要配置的位址，從 16 開始
}

impl SymbolTable {
    pub fn new() -> Self {
        let mut table = HashMap::new();
        for i in 0..16u16 {
            table.insert(format!("R{}", i), i);
        }
        table.insert("SP".to_string(), 0);
        table.insert("LCL".to_string(), 1);
        table.insert("ARG".to_string(), 2);
        table.insert("THIS".to_string(), 3);
        table.insert("THAT".to_string(), 4);
        table.insert("SCREEN".to_string(), 16384);
        table.insert("KBD".to_string(), 24576);
        SymbolTable { table, next_var: 16 }
    }

    /// 加入標籤（第一次掃描用）
    pub fn add_label(&mut self, name: &str, address: u16) -> Result<(), String> {
        if self.table.contains_key(name) {
            return Err(format!("標籤重複定義：\"{}\"", name));
        }
        self.table.insert(name.to_string(), address);
        Ok(())
    }

    /// 查符號；查不到就當成新變數，配置下一個位址（第二次掃描用）
    pub fn get_or_add_variable(&mut self, name: &str) -> u16 {
        if let Some(&addr) = self.table.get(name) {
            return addr;
        }
        let addr = self.next_var;
        self.table.insert(name.to_string(), addr);
        self.next_var += 1;
        addr
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_predefined() {
        let mut t = SymbolTable::new();
        assert_eq!(t.get_or_add_variable("R13"), 13);
        assert_eq!(t.get_or_add_variable("SCREEN"), 16384);
        assert_eq!(t.get_or_add_variable("KBD"), 24576);
        assert_eq!(t.get_or_add_variable("THAT"), 4);
    }

    #[test]
    fn test_variables_start_at_16() {
        let mut t = SymbolTable::new();
        assert_eq!(t.get_or_add_variable("i"), 16);
        assert_eq!(t.get_or_add_variable("sum"), 17);
        assert_eq!(t.get_or_add_variable("i"), 16);
    }

    #[test]
    fn test_label() {
        let mut t = SymbolTable::new();
        t.add_label("LOOP", 4).unwrap();
        assert_eq!(t.get_or_add_variable("LOOP"), 4);
        assert!(t.add_label("LOOP", 9).is_err());
    }
}
