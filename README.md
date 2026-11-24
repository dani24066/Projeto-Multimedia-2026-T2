# Projeto-Multimedia-2026-T2
Projeto multimedia 1º periodo - progrmar com IA

Nome da Aplicação / Dashboard Web: Multi·Lab
Disciplina: Oficina de Multimédia - 12.o Ano - CRSI
Ano Letivo: 2026/2027
Autor: Daniel Ferreiro Cardoso
Turma: 12ºD
Link da Aplicação Web: Link do GitHub Pages 

1. Visão Geral do Projeto

Descrição: O Meu Dashboard Apresenta 3 widgets. 2 têm funcionalidades adaptadas a alunos de Design, e o 3º é um jogo de sudoku.

Proposta Escolhida: Proposta 1 (Com alteração no 3º widget)

2. Estrutura do Código e Funcionalidades Integradas

O primeiro widget (Nuvem de Palavras-Laboratório de Design) foi construido a partir do código da nuvem de palavras ensinado da aula. 
Este widget inclui, para além das funcionalidades costruidas em aula, funcionalidades de paleta de cor, organisão de composição, verificação de contraste, 
um sujestor de sinónimos às palavras intrudozidas. e uma Ficha do Sistema do desgin que demonstra os conceitos de: Grelha; Tipografia; Cor; Acessibilidade e Princípios

O segundo widget (Ferramentas de Ecrã e Cor – Laboratório de Design) foi construído a partir do código de classificação de resolução em Python ensinado em aula. 
Este widget inclui, para além das funcionalidades da base (categorias de resolução de SD a 8K, cálculo de proporções e seletor de paletas em hexadecimal), um verificador de contraste WCAG com correção automática da 
cor, uma simulação de daltonismo, escalas de tons com valores CMYK, um conversor de unidades, uma escala tipográfica modular, uma calculadora de papel e impressão com sangria, uma grelha de colunas e a proporção 
áurea. Cada separador inclui ainda Notas de Design que explicam os conceitos de Resolução, Proporção, Cor, Tipografia, Impressão, Grelha e Acessibilidade, para que o estudante perceba o princípio por trás de cada 
ferramenta.

O terceiro widget ( Sudoku- Um jogo calmo) dispõe a partir de código gerado pela IA, do jogo base do sudoku assim como instruções de como jogar, uma paleta de cores versátil a paletas Claras e Pasteis e paletas Escuras e Suaves. Dispõe ainda de a acessibilidade de escolha de idoma entre o Português, o Espanhol, e o Inglês


3. Registo de Utilização da IA

Para demonstrares como trabalhaste em parceria com o Copilot, Gemini, Claude,
Mistral, etc., regista:

- Prompt para conversão Web/HTML:
      - Nuvem de palavras: ("transcreve este codigo para html com uma maneira aprasivel de intergir numa "página" web" / "no codigo da criação de nuvem de palavras cria uma aparencia didatica, apelativa, normativa e aprasivel a um estudante de design") 
      - Ferramentas de Ecrã e cor: ("transcreve este codigo para html com uma maneira aprasivel de intergir numa "página" web" / "no widget de Ferramentas de Ecrã e Cor; amplia a aparência e apropria-a a um estudante de desgin")
      -Jogo de Sudoku: ("A partir do código python, transcreve para html, e dá-lhe uma apareencia que se assemalhe a este website, https://cozysudoku.com , e acrescenta a possibilidade de alturar a pelate de cor de tema da interface")
      -Dashboard: ("A partir das imagens deste website: https://www.behance.net/gallery/32128635/Orbit-Space-Game-UI?utm_source=Pinterest&utm_medium=organic Cria um dashboard em que eu possa incluir o widget que criamos da nuvem de palavra, o widget da ferramentas de ecrã e de cor, e do widget do jogo de sudoku")

- Prompt para ampliação e construção de funcionalidades:
      -Nuvem de palavras: ("Otimiza o código em anexo tornando-o mais versátil a outros texto e aprofundando-o para mais customizações na criação da word cloud" / "adiciona também um sugestor de sinonimos para todas as palavras que o utilizador introduz na word cloud" / "acrescenta funcionalidades aptas a um estudante de design")
      - Ferramentas de Ecrã e Cor: ("Otimiza o código a anexo, aprundado-o a aptidões funcionais e características de o uso para o design e multimédia")
      - Jogo de Sudoku: ("Cria o código em python de um jogo de sudoku" / "A partir desse código, otimiza-o e adiciona a funcionalidade de um botao que apresente as regras do sudoku, e outro que permita ao utilizador escolher o idioma que quer utilizar ( Português, Espanhol ou Ingles).

      
- Dificuldades e erros corrigidos com a IA:
  -No widget da ferramentas de ecrã e cor pedi à IA para retirar várias funcionalidades que não considerei que fossem muito pertinente à matéria do projeto.
  
- Otimização de Layout:
  -Apesar de não ter pedido mudanças expecificas à IA no layout da web page, quando precisava de alterações, inspecionava o código e fazia-as eu mesmo, eu tentei com vários layouts diferentes até encontrar um que eu considerava pertinente para o trabalho.

4. Estrutura de Ficheiros do Repositório
Listagem simples dos ficheiros presentes na pasta:
- Ferramentas de ecrã e cor.html – Codigo html da App de ferramentas de ecrã e cor.
- Multimádia-Lab  Dashboard.html - Código html do Dashboard
- Nuvem de palavras.html - Código html da App de Nuvem de palavras
- Nuvem de palavras.py- Código de python da App da nuvem de palavras.
- README.md - Este relatório de projeto.
- Sudoku.html - Código html do jogo de sudoku
- Sudoku.py - Código python do jogo de sudoku
- ferramentas_ecra.py - Codigo py da App de ferramentas de ecrã e cor.


5. Reflexão Crítica e Aprendizagem

Desenvolve um pequeno texto refletivo sobre o projeto que inclua:
O que correu melhor foi ver o código simples da aula crescer até se tornar um conjunto completo de ferramentas. Comecei com uma nuvem de palavras e um classificador de resolução em Python e terminei com widgets em HTML, um Sudoku e um dashboard. Gostei de ligar a programação ao design. Aprendi também a separar a lógica do programa da interface, o que facilitou a passagem do Python para o HTML. A maior dificuldade foi mudar de Python para HTML e CSS, que funcionam de forma diferente e reagem em tempo real. Surgiram erros, como um nome de função repetido que impedia a página de funcionar. A IA mudou a minha forma de programar: em vez de escrever tudo linha a linha, descrevo o que quero, avalio o resultado e peço melhorias. Também me serviu de professora, ao explicar o código e os conceitos de design enquanto os escrevia. Aprendi, porém, que tenho de testar e perceber tudo o que ela produz, porque a responsabilidade pelo resultado continua a ser minha.
