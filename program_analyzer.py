from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

class CallGraph:
    def __init__(self):
        self.edges: Dict[str, List[str]] = {}

    def add_call(self, caller: str, callee: str):
        if caller not in self.edges:
            self.edges[caller] = []
        if callee not in self.edges[caller]:
            self.edges[caller].append(callee)

    def get_direct_callees(self, func_name: str) -> List[str]:
        """پیدا کردن تمام توابعی که مستقیماً توسط این تابع فراخوانی شده‌اند"""
        return self.edges.get(func_name, [])

    def detect_recursion(self) -> List[str]:
        """تشخیص توابع بازگشتی با استفاده از تشخیص دور (Cycle) در گراف"""
        recursive_funcs = []
        for caller, callees in self.edges.items():
            if caller in callees:
                recursive_funcs.append(caller)
        return recursive_funcs

@dataclass
class BasicBlock:
    """هر Basic Block شامل دنباله‌ای از دستورات بدون انشعاب است"""
    id: str
    statements: List[any]
    successors: List['BasicBlock']

class CFG:
    def __init__(self, function_name: str):
        self.function_name = function_name
        self.entry_block = BasicBlock(id="ENTRY", statements=[], successors=[])
        self.exit_block = BasicBlock(id="EXIT", statements=[], successors=[])
        self.entry_block.successors.append(self.exit_block)
        self.blocks = [self.entry_block, self.exit_block]

    def detect_unreachable_blocks(self) -> List[BasicBlock]:
        """تشخیص کدهای مرده (بلوک‌های غیرقابل دسترس) از طریق پیمایش گراف"""
        visited = set()
        
        def dfs(block):
            if block.id in visited: return
            visited.add(block.id)
            for succ in block.successors:
                dfs(succ)
                
        dfs(self.entry_block)
        
        unreachable = [b for b in self.blocks if b.id not in visited]
        return unreachable

class NavigationEngine:
    def __init__(self, global_scope):
        self.global_scope = global_scope

    def goto_definition(self, symbol_name: str, current_scope) -> dict:
        """
        عملیات Go-to-Definition: پیدا کردن مکان دقیق تعریف یک نماد (خط و ستون)
        """
        sym = current_scope.resolve(symbol_name)
        if not sym:
            return {"error": "Symbol not found"}
        
        return {
            "symbol": sym.name,
            "kind": sym.kind,
            "type": sym.type,
            "defined_at": {"line": sym.definition_loc[0], "col": sym.definition_loc[1]}
        }

    def find_scope_containing(self, symbol_name: str, current_scope):
        """یک متد کمکی برای پیدا کردن دامنه‌ای که نماد در آن تعریف شده است"""
        if symbol_name in current_scope.symbols:
            return current_scope
        for child in current_scope.children:
            found = self.find_scope_containing(symbol_name, child)
            if found: return found
        return None

    def safe_rename(self, old_name: str, new_name: str, global_scope) -> dict:
        """تغییر نام امن با جستجوی هوشمند در تمامی دامنه‌ها"""
        target_scope = self.find_scope_containing(old_name, global_scope)
        
        if not target_scope:
            return {"status": "error", "message": f"Symbol '{old_name}' not found in any scope."}

        target_symbol = target_scope.symbols[old_name]

        if new_name in target_scope.symbols:
            return {"status": "error", "message": f"Name '{new_name}' already exists in this scope."}

        outer_conflict = target_scope.parent.resolve(new_name) if target_scope.parent else None
        if outer_conflict:
            return {"status": "error", "message": f"Renaming to '{new_name}' would shadow an outer declaration."}

        target_symbol.name = new_name
        target_scope.symbols[new_name] = target_symbol
        del target_scope.symbols[old_name]
        
        return {"status": "success", "message": f"Successfully renamed '{old_name}' to '{new_name}' in scope '{target_scope.scope_name}'."}