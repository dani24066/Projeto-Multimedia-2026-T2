#!/usr/bin/env python3
"""
Gerador de nuvens de palavras (word cloud) configurável.

Instalação das dependências:
    pip install wordcloud matplotlib numpy pillow nltk
(os dados do WordNet para os sinónimos são descarregados automaticamente
 na primeira utilização de --sinonimos; é preciso ligação à Internet só nessa vez)

Exemplos de utilização:
    # Texto por omissão (a frase original)
    python nuvem_de_palavras.py

    # Texto diretamente na linha de comandos
    python nuvem_de_palavras.py -t "Estar em toda a parte onde houver bem a fazer"

    # A partir de um ficheiro, com máscara, cor única e stopwords extra
    python nuvem_de_palavras.py -f livro.txt -m silhueta.png --cor-unica "#FFD700" \
        --stopwords-extra "então,pois,assim" -o resultado.png

    # A partir de um CSV de frequências (palavra,frequencia)
    python nuvem_de_palavras.py --frequencias frequencias.csv --colormap viridis

    # Sugerir sinónimos para todas as palavras da nuvem
    python nuvem_de_palavras.py -f texto.txt --sinonimos --max-sinonimos 8

    # Escolher sinónimos palavra a palavra e regenerar a nuvem com as trocas
    python nuvem_de_palavras.py -f texto.txt --interativo

    # Exportar as sugestões para CSV
    python nuvem_de_palavras.py -f texto.txt --sinonimos-csv sugestoes.csv --sem-ecra

    # Guardar em SVG (vetorial) sem abrir a janela
    python nuvem_de_palavras.py -f texto.txt -o nuvem.svg --sem-ecra

Também pode ser importado como módulo:
    from nuvem_de_palavras import gerar_nuvem
"""

from __future__ import annotations

import argparse
import csv
import sys
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from wordcloud import STOPWORDS, ImageColorGenerator, WordCloud

TEXTO_PADRAO = (
    "Estar em toda a parte onde houver bem a fazer e sofrimento a aliviar"
)

# Lista base de stopwords em português (artigos, preposições, pronomes, etc.)
STOPWORDS_PT = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "e", "ou", "mas", "se",
    "que", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "num", "numa", "por", "pelo", "pela", "pelos", "pelas", "para", "com",
    "sem", "sobre", "entre", "até", "ao", "aos", "à", "às", "como", "quando",
    "onde", "porque", "ser", "estar", "foi", "são", "era", "há", "ter",
    "tem", "tinha", "eu", "tu", "ele", "ela", "nós", "eles", "elas", "me",
    "te", "lhe", "nos", "isto", "isso", "aquilo", "este", "esta", "esse",
    "essa", "aquele", "aquela", "meu", "minha", "seu", "sua", "mais",
    "menos", "muito", "já", "não", "sim", "também", "ainda", "só", "toda",
    "todo", "todas", "todos",
}


# --------------------------------------------------------------------------
# Leitura de dados
# --------------------------------------------------------------------------
def ler_ficheiro(caminho: str) -> str:
    """Lê um ficheiro de texto tentando UTF-8 e, se falhar, Latin-1."""
    p = Path(caminho)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")


def ler_frequencias(caminho: str) -> dict[str, float]:
    """Lê um CSV com duas colunas (palavra, frequência); ignora cabeçalhos."""
    freq: dict[str, float] = {}
    with open(caminho, newline="", encoding="utf-8") as f:
        for linha in csv.reader(f):
            if len(linha) < 2:
                continue
            try:
                freq[linha[0].strip()] = float(linha[1].replace(",", "."))
            except ValueError:
                continue  # cabeçalho ou linha inválida
    if not freq:
        raise ValueError(f"Nenhuma frequência válida encontrada em {caminho}")
    return freq


def construir_stopwords(
    usar_pt: bool, usar_en: bool, extra: list[str], ficheiro: str | None
) -> set[str]:
    """Junta as várias fontes de stopwords num único conjunto (minúsculas)."""
    s: set[str] = set()
    if usar_pt:
        s |= STOPWORDS_PT
    if usar_en:
        s |= set(STOPWORDS)
    s |= {p.strip().lower() for p in extra if p.strip()}
    if ficheiro:
        s |= {
            linha.strip().lower()
            for linha in ler_ficheiro(ficheiro).splitlines()
            if linha.strip()
        }
    return s


def carregar_mascara(caminho: str) -> np.ndarray:
    """Abre uma imagem como máscara (áreas brancas/transparentes = sem texto)."""
    img = Image.open(caminho)
    if img.mode in ("RGBA", "LA") or "transparency" in img.info:
        fundo = Image.new("RGBA", img.size, (255, 255, 255, 255))
        fundo.alpha_composite(img.convert("RGBA"))
        img = fundo
    return np.array(img.convert("RGB"))


# --------------------------------------------------------------------------
# Sugestor de sinónimos (WordNet multilingue via NLTK)
# --------------------------------------------------------------------------
def _carregar_wordnet(idioma: str):
    """Devolve o WordNet pronto a usar, descarregando os dados se for preciso."""
    try:
        from nltk.corpus import wordnet as wn
        import nltk
    except ImportError as erro:
        raise RuntimeError(
            "Para os sinónimos é preciso instalar o NLTK: pip install nltk"
        ) from erro

    for tentativa in range(2):
        try:
            wn.synsets("casa", lang=idioma)  # força o carregamento dos dados
            return wn
        except LookupError:
            if tentativa == 1:
                break
            print("A descarregar dados do WordNet (só acontece uma vez)...")
            for pacote in ("wordnet", "omw-1.4"):
                nltk.download(pacote, quiet=True)
    raise RuntimeError(
        "Não foi possível obter os dados do WordNet. Verifica a ligação à "
        "Internet ou corre: python -m nltk.downloader wordnet omw-1.4"
    )


def _formas_base(palavra: str, idioma: str) -> list[str]:
    """Palavra original + possíveis formas base (singular, masculino)."""
    p = palavra.lower()
    formas = [p]
    if idioma == "por":
        regras = [("ões", "ão"), ("ães", "ão"), ("ãos", "ão"), ("ais", "al"),
                  ("eis", "el"), ("ns", "m"), ("res", "r"), ("zes", "z"),
                  ("s", ""), ("a", "o")]
        for sufixo, subst in regras:
            if p.endswith(sufixo) and len(p) > len(sufixo) + 2:
                formas.append(p[: -len(sufixo)] + subst)
    return formas


@lru_cache(maxsize=None)
def sugerir_sinonimos(palavra: str, idioma: str = "por", maximo: int = 5) -> tuple:
    """Devolve até `maximo` sinónimos de `palavra` (tuplo vazio se não houver).

    Usa a palavra tal como está; só se não encontrar nada tenta formas base
    simples (plural -> singular, etc.). Os verbos conjugados não são
    reconhecidos: funciona melhor com infinitivos, nomes e adjetivos.
    """
    wn = _carregar_wordnet(idioma)
    for forma in _formas_base(palavra, idioma):
        encontrados: list[str] = []
        for synset in wn.synsets(forma, lang=idioma):
            for nome in synset.lemma_names(idioma):
                candidato = nome.replace("_", " ")
                if candidato.lower() not in {forma, palavra.lower(), *map(str.lower, encontrados)}:
                    encontrados.append(candidato)
        if encontrados:
            return tuple(encontrados[:maximo])
    return ()


def sugerir_para_nuvem(wc: WordCloud, idioma: str, maximo: int) -> dict[str, list[str]]:
    """Sinónimos para todas as palavras que aparecem na nuvem."""
    return {p: list(sugerir_sinonimos(p, idioma, maximo)) for p in wc.words_}


def imprimir_sugestoes(wc: WordCloud, sugestoes: dict[str, list[str]]) -> None:
    print("\n=== Sugestões de sinónimos (da palavra mais à menos frequente) ===")
    largura = max(len(p) for p in sugestoes)
    for palavra, sins in sugestoes.items():
        texto = ", ".join(sins) if sins else "(sem sugestões)"
        print(f"  {palavra:<{largura}}  ({wc.words_[palavra]:.2f})  ->  {texto}")
    print()


def exportar_sugestoes(wc: WordCloud, sugestoes: dict[str, list[str]], destino: str) -> None:
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: abre bem no Excel
        w = csv.writer(f)
        w.writerow(["palavra", "peso", "sinonimos"])
        for palavra, sins in sugestoes.items():
            w.writerow([palavra, f"{wc.words_[palavra]:.4f}", "; ".join(sins)])
    print(f"Sugestões guardadas em: {destino}")


def escolher_substituicoes(
    pesos: dict[str, float], sugestoes: dict[str, list[str]]
) -> dict[str, float]:
    """Pergunta, palavra a palavra, se o utilizador quer trocar por um sinónimo."""
    print("Para cada palavra: número = usar esse sinónimo | texto = usar outra "
          "palavra | Enter = manter | q = terminar")
    novas: dict[str, float] = {}
    parar = False
    for palavra, peso in pesos.items():
        escolha = palavra
        opcoes = sugestoes.get(palavra, [])
        if opcoes and not parar:
            lista = " | ".join(f"{i}) {s}" for i, s in enumerate(opcoes, 1))
            try:
                resp = input(f"'{palavra}' -> {lista}\n  > ").strip()
            except EOFError:
                resp, parar = "", True
            if resp.lower() == "q":
                parar = True
            elif resp.isdigit() and 1 <= int(resp) <= len(opcoes):
                escolha = opcoes[int(resp) - 1]
            elif resp:
                escolha = resp
        novas[escolha] = novas.get(escolha, 0) + peso  # junta se houver colisões
    return novas


# --------------------------------------------------------------------------
# Geração
# --------------------------------------------------------------------------
def gerar_nuvem(
    texto: str | None = None,
    frequencias: dict[str, float] | None = None,
    *,
    largura: int = 800,
    altura: int = 400,
    fundo: str | None = "#0A873A",
    colormap: str = "YlOrBr",
    cor_unica: str | None = None,
    max_palavras: int = 100,
    tamanho_min_palavra: int = 0,
    fonte_max: int | None = 200,
    fonte_min: int = 4,
    caminho_fonte: str | None = None,
    stopwords: set[str] | None = None,
    mascara: np.ndarray | None = None,
    cores_da_mascara: bool = False,
    contorno_largura: float = 0,
    contorno_cor: str = "black",
    horizontal: float = 0.9,
    relative_scaling: float = 0.5,
    colocacoes: bool = False,
    normalizar_plurais: bool = False,
    escala: float = 1.0,
    semente: int | None = 42,
) -> WordCloud:
    """Cria e devolve um objeto WordCloud. Usa `texto` OU `frequencias`."""
    if not texto and not frequencias:
        raise ValueError("É necessário fornecer 'texto' ou 'frequencias'.")

    wc = WordCloud(
        width=largura,
        height=altura,
        background_color=fundo,          # None + mode="RGBA" => fundo transparente
        mode="RGBA" if fundo is None else "RGB",
        colormap=colormap,
        max_words=max_palavras,
        min_word_length=tamanho_min_palavra,
        max_font_size=fonte_max,
        min_font_size=fonte_min,
        font_path=caminho_fonte,
        stopwords=stopwords or set(),
        mask=mascara,
        contour_width=contorno_largura,
        contour_color=contorno_cor,
        prefer_horizontal=horizontal,    # 1.0 = só horizontais; 0 = só verticais
        relative_scaling=relative_scaling,
        collocations=colocacoes,         # evita pares repetidos tipo "bem fazer"
        normalize_plurals=normalizar_plurais,
        scale=escala,                    # multiplica a resolução final
        random_state=semente,            # mesma semente => mesma disposição
    )

    if frequencias:
        wc.generate_from_frequencies(frequencias)
    else:
        wc.generate(texto)

    # Colorização (por ordem de prioridade): cor única > cores da máscara > colormap
    if cor_unica:
        wc.recolor(color_func=lambda *a, **k: cor_unica)
    elif cores_da_mascara and mascara is not None:
        wc.recolor(color_func=ImageColorGenerator(mascara))

    return wc


def guardar(wc: WordCloud, destino: str) -> None:
    """Guarda a nuvem; se a extensão for .svg grava em formato vetorial."""
    if destino.lower().endswith(".svg"):
        Path(destino).write_text(wc.to_svg(embed_font=True), encoding="utf-8")
    else:
        wc.to_file(destino)


def mostrar(wc: WordCloud, titulo: str | None = None) -> None:
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    if titulo:
        plt.title(titulo)
    plt.tight_layout()
    plt.show()  # <- os parênteses são obrigatórios (no original faltavam)


# --------------------------------------------------------------------------
# Linha de comandos
# --------------------------------------------------------------------------
def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Gera nuvens de palavras personalizáveis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    fonte = p.add_argument_group("origem dos dados")
    fonte.add_argument("-t", "--texto", help="texto diretamente na linha de comandos")
    fonte.add_argument("-f", "--ficheiro", help="ficheiro .txt com o texto")
    fonte.add_argument("--frequencias", help="CSV com colunas palavra,frequencia")

    sw = p.add_argument_group("stopwords")
    sw.add_argument("--stopwords-extra", default="em,a,e",
                    help="palavras a remover, separadas por vírgulas")
    sw.add_argument("--stopwords-ficheiro", help="ficheiro com uma palavra por linha")
    sw.add_argument("--sem-stopwords-pt", action="store_true",
                    help="não usar a lista base de português")
    sw.add_argument("--stopwords-en", action="store_true",
                    help="incluir também as stopwords de inglês")

    ap = p.add_argument_group("aparência")
    ap.add_argument("--largura", type=int, default=800)
    ap.add_argument("--altura", type=int, default=400)
    ap.add_argument("--fundo", default="#0A873A",
                    help="cor de fundo (hex/nome) ou 'transparente' (só PNG)")
    ap.add_argument("--colormap", default="YlOrBr",
                    help="ex.: viridis, plasma, inferno, magma, cividis, Greys, "
                         "Blues, Greens, Oranges, Reds, YlOrBr, YlGnBu, tab10...")
    ap.add_argument("--cor-unica", help='todas as palavras da mesma cor, ex. "#FFD700"')
    ap.add_argument("--fonte", help="caminho para um ficheiro .ttf/.otf")
    ap.add_argument("--max-palavras", type=int, default=100)
    ap.add_argument("--min-letras", type=int, default=0,
                    help="ignora palavras mais curtas do que isto")
    ap.add_argument("--fonte-max", type=int, default=200)
    ap.add_argument("--fonte-min", type=int, default=4)
    ap.add_argument("--horizontal", type=float, default=0.9,
                    help="proporção de palavras horizontais (0 a 1)")
    ap.add_argument("--relative-scaling", type=float, default=0.5,
                    help="0 = tamanho só pelo ranking; 1 = proporcional à frequência")
    ap.add_argument("--colocacoes", action="store_true",
                    help="permite pares de palavras (bigramas)")
    ap.add_argument("--normalizar-plurais", action="store_true")
    ap.add_argument("--escala", type=float, default=1.0,
                    help="multiplicador de resolução (ex.: 2 = dupla)")
    ap.add_argument("--semente", type=int, default=42,
                    help="semente aleatória (altera para variar a disposição)")

    mk = p.add_argument_group("máscara")
    mk.add_argument("-m", "--mascara", help="imagem que define a forma da nuvem")
    mk.add_argument("--cores-da-mascara", action="store_true",
                    help="usa as cores da imagem da máscara")
    mk.add_argument("--contorno", type=float, default=0, help="espessura do contorno")
    mk.add_argument("--contorno-cor", default="black")

    sn = p.add_argument_group("sinónimos")
    sn.add_argument("--sinonimos", action="store_true",
                    help="mostra sinónimos para todas as palavras da nuvem")
    sn.add_argument("--interativo", action="store_true",
                    help="permite trocar palavras por sinónimos e regenera a nuvem")
    sn.add_argument("--sinonimos-csv", help="exporta as sugestões para um CSV")
    sn.add_argument("--max-sinonimos", type=int, default=5,
                    help="máximo de sinónimos por palavra")
    sn.add_argument("--idioma-sinonimos", default="por",
                    help="código do idioma no WordNet (por, spa, fra, ita, eng...)")

    sd = p.add_argument_group("saída")
    sd.add_argument("-o", "--saida", default="Nuvem_de_Palavras.png",
                    help="ficheiro de saída (.png, .jpg ou .svg)")
    sd.add_argument("--titulo", help="título na janela do matplotlib")
    sd.add_argument("--sem-ecra", action="store_true", help="não abrir a janela")
    return p


def main() -> int:
    args = criar_parser().parse_args()

    try:
        texto = frequencias = None
        if args.frequencias:
            frequencias = ler_frequencias(args.frequencias)
        elif args.ficheiro:
            texto = ler_ficheiro(args.ficheiro)
        else:
            texto = args.texto or TEXTO_PADRAO

        opcoes = dict(
            largura=args.largura, altura=args.altura,
            fundo=None if args.fundo.lower() == "transparente" else args.fundo,
            colormap=args.colormap, cor_unica=args.cor_unica,
            max_palavras=args.max_palavras, tamanho_min_palavra=args.min_letras,
            fonte_max=args.fonte_max, fonte_min=args.fonte_min,
            caminho_fonte=args.fonte,
            stopwords=construir_stopwords(
                usar_pt=not args.sem_stopwords_pt,
                usar_en=args.stopwords_en,
                extra=args.stopwords_extra.split(","),
                ficheiro=args.stopwords_ficheiro,
            ),
            mascara=carregar_mascara(args.mascara) if args.mascara else None,
            cores_da_mascara=args.cores_da_mascara,
            contorno_largura=args.contorno, contorno_cor=args.contorno_cor,
            horizontal=args.horizontal, relative_scaling=args.relative_scaling,
            colocacoes=args.colocacoes, normalizar_plurais=args.normalizar_plurais,
            escala=args.escala, semente=args.semente,
        )
        wc = gerar_nuvem(texto, frequencias, **opcoes)

        # --- sinónimos ---
        if args.sinonimos or args.interativo or args.sinonimos_csv:
            sugestoes = sugerir_para_nuvem(wc, args.idioma_sinonimos, args.max_sinonimos)
            if args.sinonimos or args.interativo:
                imprimir_sugestoes(wc, sugestoes)
            if args.sinonimos_csv:
                exportar_sugestoes(wc, sugestoes, args.sinonimos_csv)
            if args.interativo:
                novas = escolher_substituicoes(dict(wc.words_), sugestoes)
                if set(novas) != set(wc.words_):
                    wc = gerar_nuvem(None, novas, **opcoes)
                    print("Nuvem regenerada com as palavras escolhidas.")
    except (OSError, ValueError, RuntimeError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    guardar(wc, args.saida)
    print(f"Nuvem guardada em: {args.saida}")

    if not args.sem_ecra:
        mostrar(wc, args.titulo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
