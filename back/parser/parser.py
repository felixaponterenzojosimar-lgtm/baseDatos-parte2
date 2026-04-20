from .lexical_analizer import LexicalAnalizer
from .syntactic_analyzer import SyntacticAnalyzer, SyntacticError
from .semantic_analyzer import SemanticAnalyzer, SemanticError

class ParseError(Exception):
    pass

class Parser:
    """
    Fachada pública del parser del proyecto.
    Mantiene la API estable mientras delega el análisis sintáctico a SyntacticAnalyzer
    y la verificación semántica a SemanticAnalyzer.
    """

    def __init__(self, sql: str):
        self.sql = sql
        self.lexical_analizer = LexicalAnalizer()
        self.syntactic_analyzer = SyntacticAnalyzer()
        self.semantic_analyzer = SemanticAnalyzer()

    def parse(self):
        tokens = self.lexical_analizer.tokenize(self.sql)
        try:
            node = self.syntactic_analyzer.parse(tokens)
        except SyntacticError as error:
            raise ParseError(str(error)) from error
        if not self.semantic_analyzer.validate(node):
            raise SemanticError(self.semantic_analyzer.error_message)
        return node
