class SyntaxHighlighter:
    COLORS = {
        'KEYWORD': '\033[1;34m',      
        'TYPE': '\033[36m',           
        'FUNCTION': '\033[33m',       
        'VARIABLE': '\033[37m',       
        'NUMBER': '\033[38;5;208m',   
        'STRING': '\033[32m',         
        'COMMENT': '\033[3m\033[90m', 
        'ERROR': '\033[4;31m',        
        'RESET': '\033[0m'            
        }

    @staticmethod
    def render_ansi(tokens, symbol_table) -> str:
        """
        رنگ‌آمیزی توکن‌ها بر اساس قوانین معنایی و ارجاع به جدول نمادها (AST-Level Highlighting)
        """
        highlighted_code = ""
        
        for tok in tokens:
            color = SyntaxHighlighter.COLORS['RESET']
            
            if tok.type == 'KEYWORD':
                if tok.lexeme in ['int', 'float', 'void', 'char']:
                    color = SyntaxHighlighter.COLORS['TYPE']
                else:
                    color = SyntaxHighlighter.COLORS['KEYWORD']
                    
            elif tok.type == 'IDENT':
                symbol = symbol_table.resolve(tok.lexeme)
                if symbol and symbol.kind == 'function':
                    color = SyntaxHighlighter.COLORS['FUNCTION']
                else:
                    color = SyntaxHighlighter.COLORS['VARIABLE']
                    
            elif tok.type in ['INT', 'FLOAT']:
                color = SyntaxHighlighter.COLORS['NUMBER']
            elif tok.type in ['STRING', 'CHAR']:
                color = SyntaxHighlighter.COLORS['STRING']
            elif tok.type in ['LINE_COMMENT', 'BLOCK_COMMENT']:
                color = SyntaxHighlighter.COLORS['COMMENT']
            elif tok.type == 'INVALID':
                color = SyntaxHighlighter.COLORS['ERROR']

            highlighted_code += f"{color}{tok.lexeme}{SyntaxHighlighter.COLORS['RESET']} "
            
            if tok.type == 'NEWLINE':
                highlighted_code += "\n"
                
        return highlighted_code

class IntellisenseEngine:
    def __init__(self, global_scope):
        self.global_scope = global_scope

    def get_completions(self, prefix: str, current_scope) -> list:
        """
        تولید لیست تکمیل خودکار با پیمایش سلسله‌مراتب دامنه‌ها (Lexical Scoping).
        """
        completions = []
        scope = current_scope
        
        while scope is not None:
            for name, sym in scope.symbols.items():
                if name.startswith(prefix):
                    completions.append({
                        "label": name,
                        "kind": sym.kind,           
                        "detail": sym.type,         
                        "sortOrder": len(name)      
                    })
            scope = scope.parent
            
        unique_completions = {c['label']: c for c in completions}
        return sorted(unique_completions.values(), key=lambda x: x['label'])

    def get_hover_info(self, name: str, current_scope) -> str:
        """
        تولید اطلاعات نمایشی برای زمانی که کاربر موس را روی یک متغیر یا تابع نگه می‌دارد (Hover)
        """
        sym = current_scope.resolve(name)
        if sym:
            return f"[{sym.kind}]\n{sym.name}: {sym.type}\nDefined at line {sym.definition_loc[0]}"
        return "Unknown symbol"