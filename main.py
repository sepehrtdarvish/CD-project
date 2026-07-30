import sys
from lexer import Lexer
from parser import Parser, FuncDecl, CallExpr
from semantic import SemanticAnalyzer
from ide_services import SyntaxHighlighter
from program_analyzer import NavigationEngine, CallGraph, CFG
import sys


def build_call_graph(ast_nodes):
    cg = CallGraph()
    current_func = None
    
    def visit(node):
        nonlocal current_func
        if not node: return
        
        if isinstance(node, FuncDecl):
            current_func = node.name.name
            visit(node.body)
            current_func = None
        elif isinstance(node, CallExpr) and current_func:
            cg.add_call(current_func, node.callee)
            for arg in node.args: visit(arg)
        elif hasattr(node, 'left') and hasattr(node, 'right'): # BinaryExpr
            visit(node.left)
            visit(node.right)
        elif hasattr(node, 'condition'): # IfStmt
            visit(node.condition)
            visit(node.then_branch)
            if node.else_branch: visit(node.else_branch)
        elif hasattr(node, 'statements'): # Block
            for stmt in node.statements: visit(stmt)
        elif hasattr(node, 'value'): # ReturnStmt
            visit(node.value)

    for node in ast_nodes:
        visit(node)
    return cg

def start_repl():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample_code = f.read()
            print(f"📄 Loaded source file: {file_path}")
        except FileNotFoundError:
            print(f"❌ Error: File '{file_path}' not found.")
            return
    else:
        sample_code = """int compute() { return factorial(5); }
        int factorial(int n) { if (n <= 1) return 1; return n * factorial(n - 1); }"""
        print("📄 Using default sample code. (Tip: You can pass a file like 'python3 main.py test.c')")
    print("🚀 Compiler REPL Started...")
    
    lexer = Lexer(sample_code)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens)
    ast_nodes = parser.parse_program()
    
    analyzer = SemanticAnalyzer()
    
    from semantic import Symbol
    
    for node in ast_nodes:
        if isinstance(node, FuncDecl):
            func_symbol = Symbol(
                name=node.name.name,
                kind="function",
                type=f"(...) -> {node.return_type}",
                definition_loc=(node.line, node.column)
            )
            analyzer.global_scope.define(func_symbol)

    for node in ast_nodes:
        analyzer.visit(node)
        
    global_scope = analyzer.global_scope
    nav_engine = NavigationEngine(global_scope)
    
    call_graph = build_call_graph(ast_nodes)

    print("✅ Ready! Commands: highlight | goto-def <name> | rename <old> <new> | callgraph | dead-code | exit\n")
    
    while True:
        try:
            user_input = input("compiler-repl> ").strip().split()
            if not user_input: continue
            
            cmd = user_input[0].lower()
            args = user_input[1:]
            
            if cmd == "exit":
                print("Bye!")
                break
            elif cmd == "highlight":
                print(SyntaxHighlighter.render_ansi(tokens, global_scope))
            elif cmd == "goto-def":
                if len(args) != 1: print("Usage: goto-def <symbol_name>")
                else: print(nav_engine.goto_definition(args[0], global_scope))
            elif cmd == "rename":
                if len(args) != 2: print("Usage: rename <old_name> <new_name>")
                else: print(nav_engine.safe_rename(args[0], args[1], global_scope))
            
            elif cmd == "callgraph":
                print("\n📈 Call Graph Analysis:")
                if not call_graph.edges:
                    print("  No function calls detected.")
                for caller, callees in call_graph.edges.items():
                    for callee in callees:
                        print(f"  {caller} -> {callee}")
                
                recursive = call_graph.detect_recursion()
                if recursive:
                    print(f"  🔄 Recursive functions detected: {', '.join(recursive)}\n")
                    
            elif cmd == "dead-code":
                print("\n🔍 Analyzing Control Flow Graph (CFG) for dead code...")
                cfg = CFG("factorial")
                unreachable = cfg.detect_unreachable_blocks()
                if not unreachable:
                    print("  ✅ No dead code (unreachable blocks) detected in the active CFG.\n")
                else:
                    for b in unreachable:
                        print(f"  ❌ Dead code block found: {b.id}")
                        
            else:
                print("Unknown command.")
        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error during execution: {e}")

if __name__ == "__main__":
    start_repl()