from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class ASTNode:
    line: int
    column: int
    type_annotation: Optional[str] = field(default=None, init=False)

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class IntLiteral(ASTNode):
    value: int

@dataclass
class BinaryExpr(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode

@dataclass
class VarDecl(ASTNode):
    var_type: str
    name: Identifier
    init_expr: Optional[ASTNode]

# نود جدید برای فراخوانی توابع
@dataclass
class CallExpr(ASTNode):
    callee: str
    args: List[ASTNode]

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode]

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    then_branch: ASTNode
    else_branch: Optional[ASTNode] = None

@dataclass
class Block(ASTNode):
    statements: List[ASTNode]

@dataclass
class FuncDecl(ASTNode):
    return_type: str
    name: Identifier
    params: List[Any]
    body: Block

# ==========================================
# تحلیل‌گر نحوی (Recursive-Descent Parser)
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def consume(self, expected_type=None, expected_lexeme=None):
        token = self.current_token()
        if expected_type and token.type != expected_type:
            self.error(f"Expected token type '{expected_type}', got '{token.type}'")
            return None
        if expected_lexeme and token.lexeme != expected_lexeme:
            self.error(f"Expected '{expected_lexeme}', got '{token.lexeme}'")
            return None
        self.pos += 1
        return token

    def error(self, message):
        tok = self.current_token()
        err_msg = f"Syntax Error at {tok.line}:{tok.column} - {message}"
        self.errors.append(err_msg)
        print(err_msg)
        self.synchronize()

    def synchronize(self):
        self.pos += 1
        while self.pos < len(self.tokens):
            if self.tokens[self.pos - 1].type == 'DELIM' and self.tokens[self.pos - 1].lexeme == ';':
                return
            next_lexeme = self.tokens[self.pos].lexeme
            if next_lexeme in ['int', 'float', 'void', 'if', 'while', 'return']:
                return
            self.pos += 1

    def parse_program(self):
        declarations = []
        while self.current_token().type != 'EOF':
            decl = self.parse_function()
            if decl:
                declarations.append(decl)
            else:
                self.pos += 1
        return declarations

    def parse_function(self):
        tok = self.current_token()
        if tok.type != 'KEYWORD' or tok.lexeme not in ['int', 'float', 'void', 'char']:
            return None
        
        ret_type = self.consume('KEYWORD').lexeme
        name_tok = self.consume('IDENT')
        if not name_tok: return None
        
        name = Identifier(name_tok.line, name_tok.column, name=name_tok.lexeme)
        
        self.consume('DELIM', '(')
        
        # آپدیت: خواندن و ذخیره پارامترها
        params = []
        if self.current_token().type == 'KEYWORD' and self.current_token().lexeme in ['int', 'float', 'char']:
            p_type = self.consume('KEYWORD').lexeme
            p_name_tok = self.consume('IDENT')
            p_ident = Identifier(p_name_tok.line, p_name_tok.column, name=p_name_tok.lexeme)
            params.append((p_type, p_ident)) # اضافه کردن به لیست پارامترها
            
        self.consume('DELIM', ')')
        
        body = self.parse_block()
        # پاس دادن params به گره FuncDecl
        return FuncDecl(tok.line, tok.column, return_type=ret_type, name=name, params=params, body=body)


    def parse_block(self):
        tok = self.consume('DELIM', '{')
        if not tok: return None
        
        statements = []
        while self.current_token().lexeme != '}' and self.current_token().type != 'EOF':
            stmt = self.parse_statement()
            if stmt: statements.append(stmt)
            
        self.consume('DELIM', '}')
        return Block(tok.line, tok.column, statements=statements)

    def parse_statement(self):
        tok = self.current_token()

        if tok.type == 'KEYWORD' and tok.lexeme in ['int', 'float', 'char']:
            var_type = self.consume('KEYWORD').lexeme
            name_tok = self.consume('IDENT')
            name = Identifier(name_tok.line, name_tok.column, name=name_tok.lexeme)
            
            init_expr = None
            if self.current_token().type == 'OP' and self.current_token().lexeme == '=':
                self.consume('OP', '=')
                init_expr = self.parse_expression()
                
            self.consume('DELIM', ';')
            return VarDecl(tok.line, tok.column, var_type=var_type, name=name, init_expr=init_expr)
        
        if tok.lexeme == 'return':
            self.consume('KEYWORD', 'return')
            expr = self.parse_expression()
            self.consume('DELIM', ';')
            return ReturnStmt(tok.line, tok.column, value=expr)
        elif tok.lexeme == 'if':
            self.consume('KEYWORD', 'if')
            self.consume('DELIM', '(')
            cond = self.parse_expression()
            self.consume('DELIM', ')')
            then_branch = self.parse_statement()
            return IfStmt(tok.line, tok.column, condition=cond, then_branch=then_branch)
        else:
            expr = self.parse_expression()
            self.consume('DELIM', ';')
            return expr

    def parse_expression(self):
        tok = self.current_token()
        left = None
        
        if tok.lexeme == '(':
            self.consume('DELIM', '(')
            left = self.parse_expression()
            self.consume('DELIM', ')')
        else:
            tok = self.consume()
            if tok.type == 'IDENT':
                if self.current_token().lexeme == '(':
                    self.consume('DELIM', '(')
                    arg = self.parse_expression()
                    self.consume('DELIM', ')')
                    left = CallExpr(tok.line, tok.column, callee=tok.lexeme, args=[arg])
                else:
                    left = Identifier(tok.line, tok.column, name=tok.lexeme)
            elif tok.type == 'INT':
                left = IntLiteral(tok.line, tok.column, value=int(tok.lexeme))
            else:
                self.error("Invalid expression")
                return None

        if self.current_token().type == 'OP':
            op_tok = self.consume('OP')
            right = self.parse_expression()
            return BinaryExpr(left.line, left.column, left=left, op=op_tok.lexeme, right=right)
        
        return left