"""Pacote do analisador educacional: scanner (Etapa 3) e parser (Etapa 4)."""

from .lexico import analisar_lexico, gerar_tokens_estruturais
from .sintatico import analisar_sintatico

__all__ = ["analisar_lexico", "gerar_tokens_estruturais", "analisar_sintatico"]
