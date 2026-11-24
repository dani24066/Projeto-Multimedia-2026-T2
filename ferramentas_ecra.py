#!/usr/bin/env python3
"""
Ferramentas de ecrã e cor:
  1. Classificador de resolução (SD, HD, Full HD, QHD, 4K, 8K)
  2. Calculador de proporções (Aspect Ratio: 16:9, 4:3, 1:1, ...)
  3. Seletor visual de paletas de cor em hexadecimal (janela gráfica com tkinter,
     com alternativa no terminal se não houver ambiente gráfico)

Só usa a biblioteca padrão do Python (3.9+). Executa:  python ferramentas_ecra.py
"""

from __future__ import annotations

import colorsys
import json
import math
import re
from math import gcd

# ==========================================================================
# 1. CLASSIFICAÇÃO DE RESOLUÇÃO
# ==========================================================================
# (largura mínima, nome) por ordem decrescente. Usa-se o lado MAIOR da imagem,
# para que uma imagem vertical (1080x1920) seja classificada como horizontal.
CATEGORIAS = [
    (7680, "8K UHD"),
    (3840, "4K Ultra HD"),
    (2560, "QHD (2K)"),
    (1920, "Full HD (FHD)"),
    (1280, "HD"),
    (1, "SD"),
]


def categoria_resolucao(largura: int, altura: int | None = None) -> str:
    """Devolve a categoria de uma resolução (pelo lado maior)."""
    lado = max(largura, altura or 0)
    if lado <= 0:
        raise ValueError("A resolução tem de ser um número positivo.")
    for minimo, nome in CATEGORIAS:
        if lado >= minimo:
            return nome
    return "SD"


def interpretar_resolucao(texto: str) -> tuple[int, int | None]:
    """Aceita '1920', '1920x1080', '1920 x 1080', '1920*1080' ou '1920,1080'."""
    t = texto.strip().lower().replace("×", "x")
    m = re.fullmatch(r"(\d+)\s*(?:[x*,; ]\s*(\d+))?", t)
    if not m:
        raise ValueError("Formato inválido. Exemplos: 1920 ou 1920x1080.")
    largura = int(m.group(1))
    altura = int(m.group(2)) if m.group(2) else None
    if largura <= 0 or (altura is not None and altura <= 0):
        raise ValueError("Os valores têm de ser maiores que zero.")
    return largura, altura


# ==========================================================================
# 2. PROPORÇÕES (ASPECT RATIO)
# ==========================================================================
RACIOS_PADRAO = {
    "1:1": (1, 1), "4:3": (4, 3), "3:2": (3, 2), "16:10": (16, 10),
    "16:9": (16, 9), "21:9": (21, 9), "4:5": (4, 5), "9:16": (9, 16),
}


def simplificar(largura: int, altura: int) -> tuple[int, int]:
    d = gcd(largura, altura)
    return largura // d, altura // d


def racio_mais_proximo(largura: int, altura: int) -> tuple[str, float]:
    """Rácio padrão mais próximo e o desvio percentual em relação a ele."""
    valor = largura / altura
    nome, (rl, ra) = min(RACIOS_PADRAO.items(), key=lambda kv: abs(valor - kv[1][0] / kv[1][1]))
    desvio = (valor / (rl / ra) - 1) * 100
    return nome, desvio


def interpretar_racio(texto: str) -> tuple[float, float]:
    m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*[:/x]\s*(\d+(?:[.,]\d+)?)\s*", texto.lower())
    if not m:
        raise ValueError("Rácio inválido. Exemplos: 16:9, 4:3, 1:1.")
    a, b = (float(g.replace(",", ".")) for g in m.groups())
    if a <= 0 or b <= 0:
        raise ValueError("O rácio tem de ter valores positivos.")
    return a, b


def dimensao_em_falta(racio: tuple[float, float], largura: int | None = None,
                      altura: int | None = None) -> tuple[float, float]:
    """Dado o rácio e UMA das dimensões, calcula a outra."""
    rl, ra = racio
    if largura and not altura:
        return largura, largura * ra / rl
    if altura and not largura:
        return altura * rl / ra, altura
    raise ValueError("Indica apenas a largura ou apenas a altura.")


def desenhar_proporcao(largura: int, altura: int) -> str:
    """Retângulo em ASCII com a proporção real (os carateres são ~2x mais altos)."""
    colunas = 40
    linhas = max(1, round(colunas * altura / largura / 2))
    if linhas > 14:
        linhas = 14
        colunas = max(6, round(linhas * 2 * largura / altura))
    rotulo = "%d:%d" % simplificar(largura, altura)
    meio = linhas // 2
    corpo = []
    for i in range(linhas):
        interior = rotulo.center(colunas) if i == meio and len(rotulo) < colunas else " " * colunas
        corpo.append("│" + interior + "│")
    return "\n".join(["┌" + "─" * colunas + "┐", *corpo, "└" + "─" * colunas + "┘"])


def relatorio_resolucao(largura: int, altura: int | None) -> None:
    print(f"\nCategoria: {categoria_resolucao(largura, altura)}")
    if altura is None:
        print("(Indica também a altura, por exemplo 1920x1080, para ver proporção e megapixels.)")
        return
    sl, sa = simplificar(largura, altura)
    nome, desvio = racio_mais_proximo(largura, altura)
    orientacao = "horizontal" if largura > altura else "vertical" if altura > largura else "quadrada"
    print(f"Dimensões: {largura} x {altura} px ({orientacao})")
    print(f"Proporção exata: {sl}:{sa}  (decimal {largura / altura:.4f})")
    if abs(desvio) < 0.5:
        print(f"Corresponde ao formato padrão {nome}.")
    else:
        print(f"Formato padrão mais próximo: {nome} (diferença de {desvio:+.1f}%).")
    print(f"Megapixels: {largura * altura / 1_000_000:.2f} MP  ({largura * altura:,} píxeis)".replace(",", " "))
    print(desenhar_proporcao(largura, altura))


def tabela_resolucoes(racio: tuple[float, float]) -> None:
    rl, ra = racio
    print(f"\nResoluções comuns para {rl:g}:{ra:g}")
    print(f"{'Largura':>8} {'Altura':>9}  Categoria")
    for largura in (640, 1280, 1920, 2560, 3840, 7680):
        altura = largura * ra / rl
        exata = abs(altura - round(altura)) < 1e-9
        print(f"{largura:>8} {altura:>9.1f}{'' if exata else '*'}  {categoria_resolucao(largura, round(altura))}")
    print("(* altura não inteira: arredonda ao píxel mais próximo)")


# ==========================================================================
# 3. CORES E PALETAS (HEXADECIMAL)
# ==========================================================================
def normalizar_hex(texto: str) -> str:
    """'#0a8', '0A873A' ou '#0a873a' -> '#0A873A'. Lança ValueError se inválido."""
    t = texto.strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{3}", t):
        t = "".join(c * 2 for c in t)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", t):
        raise ValueError(f"Cor hexadecimal inválida: {texto!r} (usa por ex. #0A873A)")
    return "#" + t.upper()


def hex_para_rgb(h: str) -> tuple[int, int, int]:
    h = normalizar_hex(h)
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def rgb_para_hex(r: float, g: float, b: float) -> str:
    return "#%02X%02X%02X" % (round(r), round(g), round(b))


def hex_para_hls(h: str) -> tuple[float, float, float]:
    r, g, b = (v / 255 for v in hex_para_rgb(h))
    return colorsys.rgb_to_hls(r, g, b)


def hls_para_hex(h: float, l: float, s: float) -> str:
    return rgb_para_hex(*(v * 255 for v in colorsys.hls_to_rgb(h % 1, min(1, max(0, l)), min(1, max(0, s)))))


def rodar_matiz(h: str, graus: float) -> str:
    matiz, luz, sat = hex_para_hls(h)
    return hls_para_hex(matiz + graus / 360, luz, sat)


def _linear(c: int) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(h: str) -> float:
    r, g, b = hex_para_rgb(h)
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def contraste(a: str, b: str) -> float:
    """Rácio de contraste WCAG entre duas cores (1 a 21)."""
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def nivel_wcag(rc: float) -> str:
    return "AAA" if rc >= 7 else "AA" if rc >= 4.5 else "AA (texto grande)" if rc >= 3 else "Insuficiente"


def cor_do_texto(fundo: str) -> str:
    """Preto ou branco, conforme o que der mais contraste sobre `fundo`."""
    return "#000000" if contraste(fundo, "#000000") >= contraste(fundo, "#FFFFFF") else "#FFFFFF"


ESQUEMAS = {
    "Complementar": [0, 180],
    "Análoga": [-30, 0, 30],
    "Tríade": [0, 120, 240],
    "Tétrade": [0, 90, 180, 270],
    "Complementar dividida": [0, 150, 210],
}


def gerar_paletas(base: str) -> dict[str, list[str]]:
    """Paletas harmónicas a partir de uma cor base."""
    base = normalizar_hex(base)
    paletas = {nome: [rodar_matiz(base, g) for g in graus] for nome, graus in ESQUEMAS.items()}
    matiz, _, sat = hex_para_hls(base)
    paletas["Monocromática"] = [hls_para_hex(matiz, l, sat) for l in (0.2, 0.35, 0.5, 0.65, 0.8)]
    return paletas


def info_cor(h: str) -> str:
    h = normalizar_hex(h)
    r, g, b = hex_para_rgb(h)
    matiz, luz, sat = hex_para_hls(h)
    cb, cp = contraste(h, "#FFFFFF"), contraste(h, "#000000")
    return (f"{h}   RGB({r}, {g}, {b})   HSL({matiz * 360:.0f}°, {sat * 100:.0f}%, {luz * 100:.0f}%)\n"
            f"Contraste com branco: {cb:.2f} ({nivel_wcag(cb)})   com preto: {cp:.2f} ({nivel_wcag(cp)})")


def bloco_ansi(h: str) -> str:
    r, g, b = hex_para_rgb(h)
    return f"\x1b[48;2;{r};{g};{b}m        \x1b[0m"


def paletas_no_terminal() -> None:
    """Alternativa sem janela: mostra blocos coloridos no terminal (truecolor)."""
    print("Escreve uma cor hexadecimal (ex.: #0A873A). Linha vazia para voltar.")
    while True:
        texto = input("Cor base: ").strip()
        if not texto:
            return
        try:
            base = normalizar_hex(texto)
        except ValueError as erro:
            print(erro)
            continue
        print("\n" + info_cor(base) + "\n")
        for nome, cores in gerar_paletas(base).items():
            print(f"{nome:<22}" + "  ".join(f"{bloco_ansi(c)} {c}" for c in cores))
        print()


def seletor_visual(cor_inicial: str = "#0A873A") -> None:
    """Janela gráfica (tkinter) para escolher uma cor e explorar paletas."""
    try:
        import tkinter as tk
        from tkinter import colorchooser, filedialog, messagebox
        raiz = tk.Tk()
    except Exception as erro:  # sem tkinter ou sem ambiente gráfico
        print(f"Não foi possível abrir a janela gráfica ({erro}). A usar o terminal.\n")
        return paletas_no_terminal()

    raiz.title("Seletor de paletas hexadecimais")
    raiz.geometry("720x640")
    estado = {"base": normalizar_hex(cor_inicial)}
    hex_var = tk.StringVar(value=estado["base"])
    msg_var = tk.StringVar(value="Clica numa cor para a copiar. Duplo clique para a usar como base.")

    topo = tk.Frame(raiz, padx=12, pady=12)
    topo.pack(fill="x")
    entrada = tk.Entry(topo, textvariable=hex_var, width=10, font=("Consolas", 16))
    entrada.pack(side="left")
    previa = tk.Label(topo, width=14, height=2, relief="solid", bd=1)
    previa.pack(side="left", padx=10)
    info = tk.Label(raiz, justify="left", anchor="w", padx=12, font=("Consolas", 10))
    info.pack(fill="x")
    area = tk.Frame(raiz, padx=12, pady=8)
    area.pack(fill="both", expand=True)
    tk.Label(raiz, textvariable=msg_var, anchor="w", padx=12, pady=6, fg="#555").pack(fill="x")

    def copiar(cor: str) -> None:
        raiz.clipboard_clear()
        raiz.clipboard_append(cor)
        msg_var.set(f"Copiado: {cor}")

    def atualizar(cor: str | None = None) -> None:
        try:
            estado["base"] = normalizar_hex(cor or hex_var.get())
        except ValueError as erro:
            msg_var.set(str(erro))
            return
        base = estado["base"]
        hex_var.set(base)
        previa.config(bg=base)
        info.config(text=info_cor(base))
        for filho in area.winfo_children():
            filho.destroy()
        for nome, cores in gerar_paletas(base).items():
            linha = tk.Frame(area)
            linha.pack(fill="x", pady=4)
            tk.Label(linha, text=nome, width=20, anchor="w").pack(side="left")
            for c in cores:
                b = tk.Button(linha, text=c, bg=c, fg=cor_do_texto(c), width=10, height=2,
                              relief="flat", command=lambda c=c: copiar(c))
                b.bind("<Double-Button-1>", lambda _e, c=c: atualizar(c))
                b.pack(side="left", padx=2)

    def escolher() -> None:
        _rgb, escolhida = colorchooser.askcolor(color=estado["base"], title="Escolher cor base")
        if escolhida:
            atualizar(escolhida)

    def guardar() -> None:
        caminho = filedialog.asksaveasfilename(defaultextension=".json", initialfile="paleta.json",
                                               filetypes=[("JSON", "*.json"), ("Texto", "*.txt")])
        if not caminho:
            return
        dados = {"base": estado["base"], "paletas": gerar_paletas(estado["base"])}
        with open(caminho, "w", encoding="utf-8") as f:
            if caminho.endswith(".txt"):
                f.write(f"Base: {dados['base']}\n")
                f.writelines(f"{n}: {', '.join(c)}\n" for n, c in dados["paletas"].items())
            else:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Guardado", f"Paleta guardada em:\n{caminho}")

    tk.Button(topo, text="Escolher cor…", command=escolher).pack(side="left")
    tk.Button(topo, text="Guardar paleta", command=guardar).pack(side="left", padx=6)
    entrada.bind("<Return>", lambda _e: atualizar())
    entrada.bind("<KeyRelease>", lambda _e: atualizar() if len(hex_var.get().lstrip("#")) in (3, 6) else None)
    atualizar()
    raiz.mainloop()


# ==========================================================================
# MENU
# ==========================================================================
def pedir(prompt: str, conversor):
    """Repete a pergunta até o utilizador dar um valor válido (Enter = cancelar)."""
    while True:
        texto = input(prompt).strip()
        if not texto:
            return None
        try:
            return conversor(texto)
        except ValueError as erro:
            print(f"  ! {erro}")


MENU = """
===== Ferramentas de ecrã e cor =====
 1) Analisar resolução (categoria, proporção, megapixels)
 2) Calcular dimensão em falta a partir de um rácio
 3) Tabela de resoluções comuns para um rácio
 4) Seletor visual de paletas (janela)
 5) Paletas no terminal
 0) Sair
"""


def main() -> None:
    while True:
        print(MENU)
        opcao = input("Opção: ").strip()
        try:
            if opcao == "1":
                r = pedir("Resolução em píxeis (ex.: 1920 ou 1920x1080): ", interpretar_resolucao)
                if r:
                    relatorio_resolucao(*r)
            elif opcao == "2":
                racio = pedir("Rácio (ex.: 16:9, 4:3, 1:1): ", interpretar_racio)
                if racio:
                    lado = input("Tens a [L]argura ou a [A]ltura? ").strip().lower()[:1]
                    valor = pedir("Valor em píxeis: ", lambda t: float(t.replace(",", ".")))
                    if valor and lado in ("l", "a"):
                        l, a = dimensao_em_falta(racio, valor if lado == "l" else None,
                                                 valor if lado == "a" else None)
                        print(f"\nResultado: {l:.1f} x {a:.1f} px  (arredondado: {round(l)} x {round(a)})")
            elif opcao == "3":
                racio = pedir("Rácio (ex.: 16:9): ", interpretar_racio)
                if racio:
                    tabela_resolucoes(racio)
            elif opcao == "4":
                seletor_visual()
            elif opcao == "5":
                paletas_no_terminal()
            elif opcao == "0":
                print("Até à próxima!")
                return
            else:
                print("Opção inválida. Escolhe um número do menu.")
        except (EOFError, KeyboardInterrupt):
            print("\nAté à próxima!")
            return


if __name__ == "__main__":
    main()
