import re
from dataclasses import dataclass
from typing import List

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int

    def __repr__(self):
        return f"Token(type='{self.type}', lexeme='{self.lexeme}', loc={self.line}:{self.column})"

class Lexer:
    KEYWORDS = {'if', 'else', 'while', 'for', 'return', 'int', 'float', 'char', 'void', 'struct'}

    # Longest match and priority is checked
    # UNTERMINATED_COMMENT and UNTERMINATED_STRING and MISMATCH for error handling
    RULES = [
        ('BLOCK_COMMENT',       r'/\*[\s\S]*?\*/'),         
        ('UNTERMINATED_COMMENT',r'/\*[\s\S]*'),             
        ('LINE_COMMENT',        r'//[^\n]*'),               
        ('STRING',              r'"(?:\\.|[^"\\])*"'),      
        ('UNTERMINATED_STRING', r'"(?:\\.|[^"\\])*\n?'),    
        ('CHAR',                r"'(?:\\.|[^'\\])'"),       
        ('FLOAT',               r'\d+\.\d+(?:[eE][+-]?\d+)?f?'),
        ('INT',                 r'\b(?:0[xX][0-9a-fA-F]+|0[bB][01]+|\d+)\b'),
        ('IDENT',               r'[a-zA-Z_][a-zA-Z0-9_]*'), 
        ('OP',                  r'==|!=|<=|>=|&&|\|\||\+=|-=|\*=|->|::|[+\-*/%<>=!&|]'), 
        ('DELIM',               r'[{}();,\[\]]'),           
        ('NEWLINE',             r'\n'),                     
        ('SKIP',                r'[ \t]+'),                 
        ('MISMATCH',            r'.'),                      
    ]

    TOK_REGEX = '|'.join('(?P<%s>%s)' % pair for pair in RULES)
    GET_TOKEN = re.compile(TOK_REGEX).match

    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.line = 1
        self.line_start = 0

    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.code):
            match = self.GET_TOKEN(self.code, self.pos)
            if not match: # for Mismatch
                break
            
            type = match.lastgroup # اسم گروه ریجکس که متچ شده مثل INT
            lexeme = match.group(type) # خود رشته مچ شده
            column = self.pos - self.line_start + 1

            if type == 'NEWLINE': # مدیریت فاصله ها و خطوط جدید
                self.line_start = match.end()
                self.line += 1
            elif type == 'SKIP' or type == 'LINE_COMMENT':
                pass

if __name__ == "__main__":
    sample_code = """
    int factorial(int n) {
        if (n <= 1) return 1;
        int x@ = 5; /* کاراکتر نامعتبر */
        return n * factorial(n - 1);
    }
    """
    
    lexer = Lexer(sample_code)
    tokens = lexer.tokenize()
    
    for tok in tokens:
        print(tok)