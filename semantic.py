from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

@dataclass
class Symbol:
    name: str
    kind: str
    type: str #type
    definition_loc: Tuple[int, int]
    is_initialized: bool = False
    is_used: bool = False

class SymbolTable: # هر موجودیتی در کد تعریف میشود مثل متغیر یا تابع یا پارامتر در این کلاس تعریف میشود.
    def __init__(self, scope_name: str, parent: Optional['SymbolTable'] = None):
        self.scope_name = scope_name
        self.parent = parent # به دامنه بیرونی اشاره میکند.
        self.symbols: Dict[str, Symbol] = {}
        self.children: List['SymbolTable'] = []

        if parent:
            parent.children.append(self)

    def define(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def resolve(self, name: str) -> Optional[Symbol]: # اگر متغیری در دامنه فعلی پیدا نشود کامپایلر
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None

class SemanticAnalyzer: # برای خرکت رو درخت تخو انتزاعی که در قبل تولید شد از الگوی طراحی visitor استفاده کردم.
    def __init__(self):
        self.global_scope = SymbolTable("Global")
        self.current_scope = self.global_scope
        self.diagnostics = []

    def visit_VarDecl(self, node): # با توجه به نوع هر گره به صورت داینامیک متد مربوط به اون رو صدا میزنه
        if node.init_expr:
            self.visit(node.init_expr)
            
        var_symbol = Symbol(
            name=node.name.name,
            kind="variable",
            type=node.var_type,
            definition_loc=(node.line, node.column),
            is_initialized=(node.init_expr is not None)
        )
        
        if not self.current_scope.define(var_symbol):
            self.report_diagnostic("Error", f"Duplicate declaration of variable '{node.name.name}'", node.line, node.column)

    def report_diagnostic(self, severity: str, message: str, line: int, column: int):# تشخیص خطاهایی مثل: استفاده از متغیری که قبلا تعریف نشده. تعریف دو متغیر هم نام در یک دامنه
        self.diagnostics.append(f"[{severity}] {line}:{column} - {message}")
        print(self.diagnostics[-1])

    def visit(self, node):
        """الگوی Visitor برای پیمایش درخت AST"""
        if node is None: return
        
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        pass


    def visit_FuncDecl(self, node): # وقتی کامپایلر به تعریف یه تابع میرسه یه سیمبل تیبل جدید میسازه و والدش رو دامنه فعلی قرار میده
        func_scope = SymbolTable(f"Function_{node.name.name}", parent=self.current_scope)
        self.current_scope = func_scope
        
        for param_type, param_name_node in node.params:
            param_symbol = Symbol(
                name=param_name_node.name,
                kind="parameter",
                type=param_type,
                definition_loc=(param_name_node.line, param_name_node.column),
                is_initialized=True
            )
            self.current_scope.define(param_symbol)

        self.visit(node.body)
        
        self.current_scope = self.current_scope.parent


    def visit_Block(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_IfStmt(self, node):
        self.visit(node.condition)
        
        if node.condition.type_annotation and node.condition.type_annotation not in ['int', 'bool']:
            self.report_diagnostic("Error", "Condition must evaluate to boolean or int", node.condition.line, node.condition.column)
            
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_Identifier(self, node):
        symbol = self.current_scope.resolve(node.name)
        if not symbol:
            self.report_diagnostic("Error", f"Undefined symbol '{node.name}'", node.line, node.column)
            node.type_annotation = "unknown"
        else:
            symbol.is_used = True
            node.type_annotation = symbol.type 

    def visit_BinaryExpr(self, node):
        self.visit(node.left)
        self.visit(node.right)
        
        left_type = node.left.type_annotation
        right_type = node.right.type_annotation
        
        if left_type and right_type and left_type != 'unknown' and right_type != 'unknown':
            if left_type != right_type:
                self.report_diagnostic("Error", f"Type mismatch: cannot apply '{node.op}' to {left_type} and {right_type}", node.line, node.column)
            else:
                node.type_annotation = left_type 

    def visit_IntLiteral(self, node):
        node.type_annotation = "int" # Annotate literal type

    def visit_CallExpr(self, node):
        func_sym = self.current_scope.resolve(node.callee)
        if not func_sym or func_sym.kind != 'function':
            self.report_diagnostic("Error", f"Undefined function '{node.callee}'", node.line, node.column)
            node.type_annotation = "unknown"
        else:
            ret_type = func_sym.type.split("->")[-1].strip()
            node.type_annotation = ret_type
            
        for arg in node.args:
            self.visit(arg)

    def visit_ReturnStmt(self, node):
        if node.value:
            self.visit(node.value)