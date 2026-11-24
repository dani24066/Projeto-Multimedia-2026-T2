#!/usr/bin/env python3
"""
Sudoku em Python (tkinter) — três dificuldades, notas, temporizador e ferramentas.

Teclado:  1-9 coloca número (ou nota, se o modo notas estiver ativo)
          Backspace/Delete/0 apaga · setas movem · N alterna notas
          H pista · P pausa · Ctrl+Z anular · Ctrl+Y refazer

Só usa a biblioteca padrão (Python 3.9+). Executa:  python sudoku.py
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:  # tkinter não instalado
    tk = None

FICHEIRO_RECORDES = Path(__file__).with_name("sudoku_recordes.json")
PISTAS_INICIAIS = {"Fácil": 38, "Média": 31, "Difícil": 26}  # nº alvo de números dados
PENALIZACAO_PISTA = 30  # segundos somados ao tempo por cada pista usada

# Índices dos "vizinhos" de cada célula (mesma linha, coluna ou caixa 3×3)
VIZINHOS = []
for _i in range(81):
    _r, _c = divmod(_i, 9)
    _v = ({_r * 9 + k for k in range(9)} | {k * 9 + _c for k in range(9)}
          | {(_r // 3 * 3 + a) * 9 + (_c // 3 * 3 + b) for a in range(3) for b in range(3)})
    _v.discard(_i)
    VIZINHOS.append(_v)


# ==========================================================================
# MOTOR: resolução e geração
# ==========================================================================
def resolver(grelha: list[int], limite: int = 1, aleatorio: bool = False):
    """Backtracking com bitmasks e escolha da célula com menos candidatos.
    Devolve (nº de soluções encontradas até `limite`, primeira solução ou None)."""
    g = list(grelha)
    linhas, colunas, caixas = [0] * 9, [0] * 9, [0] * 9
    for i, v in enumerate(g):
        if v:
            r, c = divmod(i, 9)
            b = (r // 3) * 3 + c // 3
            bit = 1 << v
            if linhas[r] & bit or colunas[c] & bit or caixas[b] & bit:
                return 0, None  # grelha inicial inválida
            linhas[r] |= bit
            colunas[c] |= bit
            caixas[b] |= bit
    vazias = [i for i, v in enumerate(g) if not v]
    estado = {"n": 0, "sol": None}

    def rec() -> bool:
        melhor, mascara, menor = None, 0, 10
        for i in vazias:
            if g[i]:
                continue
            r, c = divmod(i, 9)
            livres = ~(linhas[r] | colunas[c] | caixas[(r // 3) * 3 + c // 3]) & 0x3FE
            n = bin(livres).count("1")
            if n < menor:
                melhor, mascara, menor = i, livres, n
                if n <= 1:
                    break
        if melhor is None:  # sem células vazias: encontrámos uma solução
            estado["n"] += 1
            if estado["sol"] is None:
                estado["sol"] = g[:]
            return estado["n"] >= limite
        if menor == 0:
            return False
        r, c = divmod(melhor, 9)
        b = (r // 3) * 3 + c // 3
        digitos = [d for d in range(1, 10) if mascara >> d & 1]
        if aleatorio:
            random.shuffle(digitos)
        for d in digitos:
            bit = 1 << d
            g[melhor] = d
            linhas[r] |= bit
            colunas[c] |= bit
            caixas[b] |= bit
            parar = rec()
            g[melhor] = 0
            linhas[r] ^= bit
            colunas[c] ^= bit
            caixas[b] ^= bit
            if parar:
                return True
        return False

    rec()
    return estado["n"], estado["sol"]


def gerar(dificuldade: str) -> tuple[list[int], list[int]]:
    """Gera (puzzle, solução). O puzzle tem sempre solução única."""
    _, completa = resolver([0] * 81, aleatorio=True)
    puzzle = completa[:]
    alvo, pistas = PISTAS_INICIAIS[dificuldade], 81
    ordem = list(range(81))
    random.shuffle(ordem)
    for i in ordem:
        if pistas <= alvo:
            break
        valor, puzzle[i] = puzzle[i], 0
        if resolver(puzzle, limite=2)[0] == 1:
            pistas -= 1
        else:
            puzzle[i] = valor  # remover tornaria a solução ambígua
    return puzzle, completa


def candidatos(valores: list[int], i: int) -> set[int]:
    return set(range(1, 10)) - {valores[j] for j in VIZINHOS[i]}


def formatar_tempo(s: int) -> str:
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# ==========================================================================
# RECORDES
# ==========================================================================
def carregar_recordes() -> dict:
    try:
        return json.loads(FICHEIRO_RECORDES.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def guardar_recorde(dificuldade: str, segundos: int) -> bool:
    """Guarda o tempo (top 5). Devolve True se for o melhor tempo desta dificuldade."""
    dados = carregar_recordes()
    tempos = sorted(dados.get(dificuldade, []) + [segundos])[:5]
    novo_recorde = tempos[0] == segundos and segundos not in dados.get(dificuldade, [])
    dados[dificuldade] = tempos
    try:
        FICHEIRO_RECORDES.write_text(json.dumps(dados, indent=2), encoding="utf-8")
    except OSError:
        pass
    return novo_recorde


# ==========================================================================
# INTERFACE
# ==========================================================================
TEMAS = {
    "claro": dict(fundo="#f4f5f2", painel="#f4f5f2", texto="#1f2937", mudo="#6b7280", celula="#ffffff",
                  sel="#ffe27a", par="#eef2e6", igual="#cfe8d5", erro="#f7c6c0", fixo="#111827",
                  jogador="#1d5fd0", pista="#7a3db8", conflito="#d0392b", nota="#6b7280",
                  fina="#c9ccc4", grossa="#1f2937", botao="#e3e6df", ativo="#ffd21e"),
    "escuro": dict(fundo="#0f1411", painel="#0f1411", texto="#e5ede7", mudo="#94a198", celula="#171e1a",
                   sel="#7a6417", par="#1d2a22", igual="#24533a", erro="#6b2a24", fixo="#f3f4f6",
                   jogador="#7db4ff", pista="#c9a0ff", conflito="#ff8a7a", nota="#94a198",
                   fina="#2f3b33", grossa="#9db0a3", botao="#222d26", ativo="#c79b00"),
}


class JogoSudoku:
    CEL, MARGEM = 58, 10

    def __init__(self, raiz: "tk.Tk"):
        self.raiz = raiz
        raiz.title("Sudoku")
        raiz.resizable(False, False)
        self.dificuldade = tk.StringVar(value="Fácil")
        self.modo_notas = tk.BooleanVar(value=False)
        self.mostrar_conflitos = tk.BooleanVar(value=True)
        self.limpar_notas = tk.BooleanVar(value=True)
        self.tema_escuro = tk.BooleanVar(value=False)
        self.estado = tk.StringVar()
        self.t = TEMAS["claro"]
        self.acumulado, self.inicio, self.a_correr = 0.0, 0.0, False
        self.pausado = self.terminado = False
        self.sel: int | None = 40
        self.erros_visiveis: set[int] = set()
        self._construir()
        raiz.bind("<Key>", self.tecla)
        raiz.bind("<Control-z>", lambda _e: self.anular())
        raiz.bind("<Control-y>", lambda _e: self.refazer_jogada())
        self.novo_jogo(confirmar=False)
        self._tick()

    # ---------- construção da janela ----------
    def _botao(self, pai, texto, comando, **kw):
        return tk.Button(pai, text=texto, command=comando, takefocus=0, relief="flat", padx=8, pady=4, **kw)

    def _construir(self) -> None:
        C, M = self.CEL, self.MARGEM
        self.cv = tk.Canvas(self.raiz, width=9 * C + 2 * M, height=9 * C + 2 * M, highlightthickness=0)
        self.cv.grid(row=0, column=0, padx=(12, 6), pady=12)
        self.cv.bind("<Button-1>", self.clique)

        p = tk.Frame(self.raiz)
        p.grid(row=0, column=1, sticky="ns", padx=(6, 12), pady=12)
        tk.Label(p, text="Sudoku", font=("Helvetica", 22, "bold")).pack(anchor="w")

        linha = tk.Frame(p)
        linha.pack(anchor="w", pady=(6, 0))
        for d in PISTAS_INICIAIS:
            tk.Radiobutton(linha, text=d, value=d, variable=self.dificuldade, takefocus=0).pack(side="left")
        self._botao(p, "Novo jogo", self.novo_jogo).pack(fill="x", pady=(6, 8))

        self.lbl_tempo = tk.Label(p, text="00:00", font=("Courier", 30, "bold"))
        self.lbl_tempo.pack(anchor="w")
        self.lbl_stats = tk.Label(p, text="", justify="left")
        self.lbl_stats.pack(anchor="w")
        self.lbl_melhor = tk.Label(p, text="", justify="left")
        self.lbl_melhor.pack(anchor="w", pady=(0, 8))

        teclado = tk.Frame(p)
        teclado.pack(pady=(0, 8))
        self.bt_dig = {}
        for d in range(1, 10):
            b = self._botao(teclado, str(d), lambda d=d: self.colocar(d), width=5, font=("Helvetica", 11, "bold"))
            b.grid(row=(d - 1) // 3, column=(d - 1) % 3, padx=2, pady=2)
            self.bt_dig[d] = b

        ferr = tk.Frame(p)
        ferr.pack(fill="x")
        self.bt_notas = tk.Checkbutton(ferr, text="✎ Notas (N)", variable=self.modo_notas, indicatoron=False,
                                       command=self.redesenhar, takefocus=0, padx=8, pady=4, relief="flat")
        self.bt_pausa = self._botao(ferr, "⏸ Pausa (P)", self.alternar_pausa)
        acoes = [self.bt_notas, self._botao(ferr, "⌫ Apagar", self.apagar),
                 self._botao(ferr, "↶ Anular", self.anular), self._botao(ferr, "↷ Refazer", self.refazer_jogada),
                 self._botao(ferr, "💡 Pista (H)", self.pista), self._botao(ferr, "✔ Verificar", self.verificar),
                 self._botao(ferr, "Notas auto", self.notas_automaticas), self.bt_pausa]
        for k, b in enumerate(acoes):
            b.grid(row=k // 2, column=k % 2, sticky="ew", padx=2, pady=2)
        ferr.columnconfigure((0, 1), weight=1)
        self._botao(p, "Mostrar solução", self.mostrar_solucao).pack(fill="x", pady=(6, 0))

        for texto, var, cmd in (("Destacar conflitos", self.mostrar_conflitos, self.redesenhar),
                                ("Limpar notas automaticamente", self.limpar_notas, None),
                                ("Tema escuro", self.tema_escuro, self.aplicar_tema)):
            tk.Checkbutton(p, text=texto, variable=var, command=cmd, takefocus=0).pack(anchor="w")
        tk.Label(p, textvariable=self.estado, wraplength=230, justify="left").pack(anchor="w", pady=(8, 0))
        self.aplicar_tema()

    def _pintar(self, w) -> None:
        t = self.t
        for f in w.winfo_children():
            cls = f.winfo_class()
            if cls in ("Frame", "Label"):
                f.configure(bg=t["painel"], **({"fg": t["texto"]} if cls == "Label" else {}))
            elif cls == "Button":
                f.configure(bg=t["botao"], fg=t["texto"], activebackground=t["ativo"], activeforeground=t["texto"])
            elif cls in ("Checkbutton", "Radiobutton"):
                cor = t["botao"] if f is self.bt_notas else t["painel"]
                f.configure(bg=cor, fg=t["texto"], activebackground=cor, activeforeground=t["texto"],
                            selectcolor=t["ativo"] if f is self.bt_notas else t["celula"])
            self._pintar(f)

    def aplicar_tema(self) -> None:
        self.t = TEMAS["escuro" if self.tema_escuro.get() else "claro"]
        self.raiz.configure(bg=self.t["fundo"])
        self.cv.configure(bg=self.t["fundo"])
        self._pintar(self.raiz)
        self.redesenhar()

    # ---------- novo jogo ----------
    def novo_jogo(self, confirmar: bool = True) -> None:
        if confirmar and not self.terminado and self.desfazer:
            if not messagebox.askyesno("Novo jogo", "Abandonar o jogo atual e começar outro?"):
                return
        self.raiz.config(cursor="watch")
        self.estado.set("A gerar puzzle…")
        self.raiz.update_idletasks()
        puzzle, self.solucao = gerar(self.dificuldade.get())
        self.raiz.config(cursor="")
        self.dado = [bool(v) for v in puzzle]
        self.valor = puzzle[:]
        self.notas = [set() for _ in range(81)]
        self.desfazer: list = []
        self.refazer: list = []
        self.erros = self.pistas = self.penalizacao = 0
        self.por_pista: set[int] = set()
        self.acumulado, self.inicio, self.a_correr = 0.0, time.monotonic(), True
        self.pausado = self.terminado = self.usou_solucao = False
        self.bt_pausa.config(text="⏸ Pausa (P)")
        self.erros_visiveis = set()
        self.estado.set(f"Nível {self.dificuldade.get()}: {sum(self.dado)} números dados. Boa sorte!")
        self.redesenhar()

    # ---------- tempo ----------
    def tempo(self) -> int:
        t = self.acumulado + (time.monotonic() - self.inicio if self.a_correr else 0)
        return int(t) + self.penalizacao

    def _tick(self) -> None:
        self.lbl_tempo.config(text=formatar_tempo(self.tempo()))
        self.raiz.after(250, self._tick)

    def _parar_relogio(self) -> None:
        if self.a_correr:
            self.acumulado += time.monotonic() - self.inicio
            self.a_correr = False

    def alternar_pausa(self) -> None:
        if self.terminado:
            return
        if self.pausado:
            self.inicio, self.a_correr, self.pausado = time.monotonic(), True, False
            self.bt_pausa.config(text="⏸ Pausa (P)")
        else:
            self._parar_relogio()
            self.pausado = True
            self.bt_pausa.config(text="▶ Continuar (P)")
        self.redesenhar()

    def _pode_jogar(self) -> bool:
        return not (self.pausado or self.terminado)

    # ---------- jogadas ----------
    def _aplicar(self, estado: dict) -> None:
        for i, (v, n) in estado.items():
            self.valor[i], self.notas[i] = v, set(n)
        self.redesenhar()

    def _alterar(self, novos: dict) -> None:
        antes = {i: (self.valor[i], frozenset(self.notas[i])) for i in novos}
        depois = {i: (v, frozenset(n)) for i, (v, n) in novos.items()}
        if antes == depois:
            return
        self._aplicar(depois)
        self.desfazer.append((antes, depois))
        self.refazer.clear()
        if self.valor == self.solucao:
            self._vitoria()

    def colocar(self, d: int) -> None:
        i = self.sel
        if not self._pode_jogar() or i is None or self.dado[i]:
            return
        if self.modo_notas.get():
            if self.valor[i] == 0:
                self._alterar({i: (0, self.notas[i] ^ {d})})
            return
        if self.valor[i] == d:  # carregar no mesmo número apaga-o
            self._alterar({i: (0, set())})
            return
        novos = {i: (d, set())}
        if self.limpar_notas.get():
            for j in VIZINHOS[i]:
                if d in self.notas[j]:
                    novos[j] = (self.valor[j], self.notas[j] - {d})
        if d != self.solucao[i]:
            self.erros += 1
            self.estado.set("Esse número não pertence aqui.")
        else:
            self.estado.set("")
        self._alterar(novos)

    def apagar(self) -> None:
        i = self.sel
        if self._pode_jogar() and i is not None and not self.dado[i] and (self.valor[i] or self.notas[i]):
            self._alterar({i: (0, set())})

    def anular(self) -> None:
        if self._pode_jogar() and self.desfazer:
            antes, depois = self.desfazer.pop()
            self.refazer.append((antes, depois))
            self._aplicar(antes)

    def refazer_jogada(self) -> None:
        if self._pode_jogar() and self.refazer:
            antes, depois = self.refazer.pop()
            self.desfazer.append((antes, depois))
            self._aplicar(depois)

    def pista(self) -> None:
        if not self._pode_jogar():
            return
        i = self.sel
        if i is None or self.dado[i] or self.valor[i] == self.solucao[i]:
            alvos = [k for k in range(81) if self.valor[k] != self.solucao[k]]
            if not alvos:
                return
            i = random.choice(alvos)
            self.sel = i
        self.pistas += 1
        self.penalizacao += PENALIZACAO_PISTA
        self.por_pista.add(i)
        self.estado.set(f"Pista usada: +{PENALIZACAO_PISTA} s ao tempo.")
        self._alterar({i: (self.solucao[i], set())})

    def verificar(self) -> None:
        if not self._pode_jogar():
            return
        self.erros_visiveis = {i for i, v in enumerate(self.valor) if v and v != self.solucao[i]}
        if self.erros_visiveis:
            self.estado.set(f"{len(self.erros_visiveis)} número(s) errado(s), assinalados a vermelho.")
            self.raiz.after(2500, self._limpar_erros)
        else:
            self.estado.set("Tudo certo até agora!")
        self.redesenhar()

    def _limpar_erros(self) -> None:
        self.erros_visiveis = set()
        self.redesenhar()

    def notas_automaticas(self) -> None:
        if not self._pode_jogar():
            return
        self._alterar({i: (0, candidatos(self.valor, i)) for i in range(81) if self.valor[i] == 0})
        self.estado.set("Notas preenchidas com todos os candidatos possíveis.")

    def mostrar_solucao(self) -> None:
        if self.terminado or not messagebox.askyesno("Mostrar solução", "Mostrar a solução? O tempo não será registado."):
            return
        self.valor, self.notas = self.solucao[:], [set() for _ in range(81)]
        self.terminado = self.usou_solucao = True
        self._parar_relogio()
        self.estado.set("Solução mostrada.")
        self.redesenhar()

    def _vitoria(self) -> None:
        self.terminado = True
        self._parar_relogio()
        segundos = self.tempo()
        texto = (f"Completaste o Sudoku {self.dificuldade.get()}!\n\nTempo: {formatar_tempo(segundos)}"
                 f"\nErros: {self.erros}   Pistas: {self.pistas}")
        if guardar_recorde(self.dificuldade.get(), segundos):
            texto += "\n\n★ Novo melhor tempo!"
        self.estado.set("Parabéns! Clica em “Novo jogo” para continuar.")
        self.redesenhar()
        messagebox.showinfo("Parabéns!", texto)

    # ---------- entrada ----------
    def clique(self, e) -> None:
        if self.pausado:
            self.alternar_pausa()
            return
        C, M = self.CEL, self.MARGEM
        c, r = (e.x - M) // C, (e.y - M) // C
        if 0 <= r < 9 and 0 <= c < 9:
            self.sel = r * 9 + c
            self.redesenhar()

    def tecla(self, e) -> None:
        if e.char and e.char in "123456789":
            self.colocar(int(e.char))
        elif e.keysym in ("BackSpace", "Delete") or e.char == "0":
            self.apagar()
        elif e.keysym in ("Up", "Down", "Left", "Right") and self.sel is not None and not self.pausado:
            r, c = divmod(self.sel, 9)
            dr, dc = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}[e.keysym]
            self.sel = ((r + dr) % 9) * 9 + (c + dc) % 9
            self.redesenhar()
        elif e.char.lower() == "n":
            self.modo_notas.set(not self.modo_notas.get())
            self.redesenhar()
        elif e.char.lower() == "h":
            self.pista()
        elif e.char.lower() == "p":
            self.alternar_pausa()

    # ---------- desenho ----------
    def _conflitos(self) -> set[int]:
        return {i for i, v in enumerate(self.valor) if v and any(self.valor[j] == v for j in VIZINHOS[i])}

    def redesenhar(self) -> None:
        cv, t, C, M = self.cv, self.t, self.CEL, self.MARGEM
        cv.delete("all")
        conflitos = self._conflitos() if self.mostrar_conflitos.get() else set()
        s = self.sel
        vs = self.valor[s] if s is not None else 0

        for i in range(81):
            r, c = divmod(i, 9)
            x, y = M + c * C, M + r * C
            if self.pausado:
                cor = t["celula"]
            elif i in self.erros_visiveis:
                cor = t["erro"]
            elif i == s:
                cor = t["sel"]
            elif vs and self.valor[i] == vs:
                cor = t["igual"]
            elif s is not None and i in VIZINHOS[s]:
                cor = t["par"]
            else:
                cor = t["celula"]
            cv.create_rectangle(x, y, x + C, y + C, fill=cor, outline="")
            if self.pausado:
                continue
            v = self.valor[i]
            if v:
                if self.dado[i]:
                    cor_t, fonte = t["fixo"], ("Helvetica", 24, "bold")
                elif i in conflitos:
                    cor_t, fonte = t["conflito"], ("Helvetica", 24)
                elif i in self.por_pista and v == self.solucao[i]:
                    cor_t, fonte = t["pista"], ("Helvetica", 24)
                else:
                    cor_t, fonte = t["jogador"], ("Helvetica", 24)
                cv.create_text(x + C / 2, y + C / 2, text=str(v), fill=cor_t, font=fonte)
            else:
                for d in self.notas[i]:
                    nx = x + C * ((d - 1) % 3 + 0.5) / 3
                    ny = y + C * ((d - 1) // 3 + 0.5) / 3
                    destaque = vs == d
                    cv.create_text(nx, ny, text=str(d), fill=t["jogador"] if destaque else t["nota"],
                                   font=("Helvetica", 9, "bold" if destaque else "normal"))

        for k in range(10):  # linhas da grelha
            grossa = k % 3 == 0
            cor, larg = (t["grossa"], 3) if grossa else (t["fina"], 1)
            cv.create_line(M + k * C, M, M + k * C, M + 9 * C, fill=cor, width=larg)
            cv.create_line(M, M + k * C, M + 9 * C, M + k * C, fill=cor, width=larg)

        if self.pausado:
            cv.create_text(M + 4.5 * C, M + 4.5 * C, text="Em pausa\nclica para continuar",
                           fill=t["texto"], font=("Helvetica", 22, "bold"), justify="center")
        self._atualizar_painel()

    def _atualizar_painel(self) -> None:
        for d, b in self.bt_dig.items():
            restantes = 9 - sum(1 for v in self.valor if v == d)
            b.config(text=f"{d}\n({max(restantes, 0)})", state="disabled" if restantes <= 0 else "normal")
        self.lbl_stats.config(text=f"Erros: {self.erros}   Pistas: {self.pistas}\n"
                                   f"Casas vazias: {self.valor.count(0)}")
        tempos = carregar_recordes().get(self.dificuldade.get(), [])
        self.lbl_melhor.config(text="Melhor tempo: " + (formatar_tempo(tempos[0]) if tempos else "—"))


def main() -> None:
    if tk is None:
        print("O tkinter não está instalado. No Linux: sudo apt install python3-tk")
        return
    raiz = tk.Tk()
    JogoSudoku(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
