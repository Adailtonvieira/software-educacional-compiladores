# software-educacional-compiladores

## Introdução

Este projeto consiste no desenvolvimento de um **software educacional para o ensino de compiladores**, com foco nas fases de análise léxica e sintática. A ferramenta é voltada a estudantes de graduação em Ciência da Computação que enfrentam dificuldades na transição entre a teoria e a prática no estudo de compiladores.

O software adota uma abordagem **web interativa**, permitindo que os alunos visualizem o processo de compilação passo a passo, desde a tokenização do código-fonte até a construção da árvore sintática. Esta primeira etapa estabelece a fundação do projeto: estrutura de pastas, ambiente Docker funcional e uma aplicação web mínima exibindo a mensagem "Hello, World!", provando que toda a cadeia (frontend + backend) está operacional.

---

## Linguagem Foco

**Python** - escolhida pela simplicidade sintática e ampla adoção acadêmica.

---

## Justificativa da Escolha

A escolha do Python como linguagem foco do software educacional baseia-se em três razões principais:

1. **Simplicidade sintática** - Python possui uma gramática limpa e legível, o que permite que o estudante concentre seus esforços na compreensão dos conceitos de compilação (análise léxica, sintática e semântica) sem se dispersar com complexidades sintáticas da própria linguagem.

2. **Disponibilidade de bibliotecas de referência** - Ferramentas como PLY e Lark oferecem implementações de analisadores que podem servir como base de comparação e inspiração para o desenvolvimento do software.

3. **Ampla adoção acadêmica** - Python é a linguagem introdutória mais utilizada em cursos de Ciência da Computação no Brasil, o que facilita a adoção do software por alunos e professores.

Além disso, a escolha de Python alinha-se ao público-alvo (graduandos em Ciência da Computação), que tipicamente já possui familiaridade com a linguagem.

---

## Subconjunto Inicial

Para tornar o projeto viável dentro do prazo da disciplina, foi delimitado um **subconjunto inicial** da linguagem Python. Não se pretende cobrir a linguagem inteira, mas sim as construções mais fundamentais:

- **Declaração de variáveis** 
- **Operadores aritméticos** 
- **Estruturas condicionais simples** 
- **Expressões de comparação**

Novas construções serão incorporadas gradativamente nas etapas seguintes do projeto, conforme a evolução do software.

---

## Estrutura do Projeto
> software-educacional-compiladores/
    > backend/ 
      >    app.py 
      >    requirements.txt 
      >    Dockerfile 

    > frontend/
      > index.html
      > nginx.conf 
      > Dockerfile 

> compose.yaml # Orquestração dos serviços com Docker Compose
> README.md




## Como Clonar e Rodar em Qualquer Máquina

Esta seção descreve o passo a passo para executar o projeto em uma máquina que nunca teve contato com ele. Qualquer pessoa com os pré-requisitos instalados conseguirá reproduzir o ambiente.

### Pré-requisitos

Antes de começar, certifique-se de que a máquina possui:

| Ferramenta     | Versão mínima | Como verificar |
| Git            | 2.30+         | `git --version` |
| Docker Desktop | 24+           | `docker --version` |
| Docker Compose | v2+           | `docker compose version` |

#### Observação para Windows

O Docker Desktop no Windows requer:

- **WSL 2** instalado e configurado
- Uma **distribuição Linux** (ex: Ubuntu) instalada no WSL

Para instalar o WSL e o Ubuntu, execute no **PowerShell como Administrador**:

```powershell
wsl --install -d Ubuntu
