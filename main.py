
import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

# Squares are 0..63, index = row * 8 + col, row 0 = rank 8, col 0 = file a.
# Pieces are single chars: uppercase = white, lowercase = black, '.' = empty.

FILES = "abcdefgh"
RANKS = "87654321"

KNIGHT_DELTAS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                 (1, -2), (1, 2), (2, -1), (2, 1)]
KING_DELTAS = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
               (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Solid glyphs used for both colours; colour comes from the fill.
GLYPH = {'K': '\u265A', 'Q': '\u265B', 'R': '\u265C',
         'B': '\u265D', 'N': '\u265E', 'P': '\u265F'}


def color_of(piece):
    if piece == '.':
        return None
    return 'w' if piece.isupper() else 'b'


def other(color):
    return 'b' if color == 'w' else 'w'


def sq_name(sq):
    return FILES[sq % 8] + RANKS[sq // 8]


class Position:
    __slots__ = ('board', 'turn', 'castling', 'ep', 'halfmove', 'fullmove')

    def __init__(self, board, turn, castling, ep, halfmove, fullmove):
        self.board = board          # list of 64 chars
        self.turn = turn            # 'w' or 'b'
        self.castling = castling    # set of 'K','Q','k','q'
        self.ep = ep                # en-passant target square or None
        self.halfmove = halfmove
        self.fullmove = fullmove

    @staticmethod
    def start():
        board = list(
            "rnbqkbnr"
            "pppppppp"
            "........"
            "........"
            "........"
            "........"
            "PPPPPPPP"
            "RNBQKBNR"
        )
        return Position(board, 'w', set("KQkq"), None, 0, 1)

    def key(self):
        return (''.join(self.board), self.turn,
                ''.join(sorted(self.castling)), self.ep)


def find_king(board, color):
    target = 'K' if color == 'w' else 'k'
    for sq, p in enumerate(board):
        if p == target:
            return sq
    return None


def is_attacked(board, sq, by):
    r, c = divmod(sq, 8)

    # pawns
    pr = r + 1 if by == 'w' else r - 1
    if 0 <= pr < 8:
        want = 'P' if by == 'w' else 'p'
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < 8 and board[pr * 8 + nc] == want:
                return True

    # knights
    want = 'N' if by == 'w' else 'n'
    for dr, dc in KNIGHT_DELTAS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr * 8 + nc] == want:
            return True

    # king
    want = 'K' if by == 'w' else 'k'
    for dr, dc in KING_DELTAS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr * 8 + nc] == want:
            return True

    # sliding pieces
    for dirs, kinds in ((BISHOP_DIRS, 'BQ'), (ROOK_DIRS, 'RQ')):
        wanted = kinds if by == 'w' else kinds.lower()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                p = board[nr * 8 + nc]
                if p != '.':
                    if p in wanted:
                        return True
                    break
                nr += dr
                nc += dc
    return False


def in_check(pos):
    ksq = find_king(pos.board, pos.turn)
    return ksq is not None and is_attacked(pos.board, ksq, other(pos.turn))


def _add_pawn_move(moves, src, dst, promoting):
    if promoting:
        for p in ('Q', 'R', 'B', 'N'):
            moves.append((src, dst, p))
    else:
        moves.append((src, dst, None))


def gen_pseudo(pos):
    b, turn = pos.board, pos.turn
    enemy = other(turn)
    moves = []

    for src, piece in enumerate(b):
        if piece == '.' or color_of(piece) != turn:
            continue
        r, c = divmod(src, 8)
        kind = piece.upper()

        if kind == 'P':
            d = -1 if turn == 'w' else 1
            home = 6 if turn == 'w' else 1
            last = 0 if turn == 'w' else 7
            nr = r + d
            if 0 <= nr < 8:
                if b[nr * 8 + c] == '.':
                    _add_pawn_move(moves, src, nr * 8 + c, nr == last)
                    if r == home and b[(r + 2 * d) * 8 + c] == '.':
                        moves.append((src, (r + 2 * d) * 8 + c, None))
                for dc in (-1, 1):
                    nc = c + dc
                    if not 0 <= nc < 8:
                        continue
                    dst = nr * 8 + nc
                    if b[dst] != '.' and color_of(b[dst]) == enemy:
                        _add_pawn_move(moves, src, dst, nr == last)
                    elif pos.ep is not None and dst == pos.ep:
                        moves.append((src, dst, None))

        elif kind == 'N':
            for dr, dc in KNIGHT_DELTAS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    dst = nr * 8 + nc
                    if color_of(b[dst]) != turn:
                        moves.append((src, dst, None))

        elif kind in ('B', 'R', 'Q'):
            dirs = (BISHOP_DIRS if kind == 'B'
                    else ROOK_DIRS if kind == 'R'
                    else BISHOP_DIRS + ROOK_DIRS)
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    dst = nr * 8 + nc
                    if b[dst] == '.':
                        moves.append((src, dst, None))
                    else:
                        if color_of(b[dst]) == enemy:
                            moves.append((src, dst, None))
                        break
                    nr += dr
                    nc += dc

        elif kind == 'K':
            for dr, dc in KING_DELTAS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    dst = nr * 8 + nc
                    if color_of(b[dst]) != turn:
                        moves.append((src, dst, None))
            # castling
            home = 60 if turn == 'w' else 4
            rook = 'R' if turn == 'w' else 'r'
            ks = 'K' if turn == 'w' else 'k'
            qs = 'Q' if turn == 'w' else 'q'
            if src == home and not is_attacked(b, home, enemy):
                if (ks in pos.castling and b[home + 3] == rook
                        and b[home + 1] == '.' and b[home + 2] == '.'
                        and not is_attacked(b, home + 1, enemy)
                        and not is_attacked(b, home + 2, enemy)):
                    moves.append((src, home + 2, None))
                if (qs in pos.castling and b[home - 4] == rook
                        and b[home - 1] == '.' and b[home - 2] == '.'
                        and b[home - 3] == '.'
                        and not is_attacked(b, home - 1, enemy)
                        and not is_attacked(b, home - 2, enemy)):
                    moves.append((src, home - 2, None))
    return moves


def make_move(pos, move):
    src, dst, promo = move
    b = pos.board[:]
    piece = b[src]
    color = color_of(piece)
    kind = piece.upper()
    castling = set(pos.castling)
    ep = None
    capture = b[dst] != '.'

    # en passant capture
    if kind == 'P' and pos.ep is not None and dst == pos.ep and b[dst] == '.':
        b[dst + (8 if color == 'w' else -8)] = '.'
        capture = True

    b[dst] = piece
    b[src] = '.'

    # promotion
    if kind == 'P' and dst // 8 in (0, 7):
        p = promo or 'Q'
        b[dst] = p if color == 'w' else p.lower()

    # double push -> en passant target
    if kind == 'P' and abs(dst // 8 - src // 8) == 2:
        ep = (src + dst) // 2

    # rook hop when castling
    if kind == 'K' and abs(dst % 8 - src % 8) == 2:
        if dst % 8 == 6:
            rs, rd = src + 3, src + 1
        else:
            rs, rd = src - 4, src - 1
        b[rd], b[rs] = b[rs], '.'

    # castling rights
    if kind == 'K':
        castling -= set('KQ') if color == 'w' else set('kq')
    for corner, right in ((63, 'K'), (56, 'Q'), (7, 'k'), (0, 'q')):
        if src == corner or dst == corner:
            castling.discard(right)

    halfmove = 0 if (kind == 'P' or capture) else pos.halfmove + 1
    fullmove = pos.fullmove + (1 if color == 'b' else 0)
    return Position(b, other(color), castling, ep, halfmove, fullmove)


def legal_moves(pos):
    out = []
    mover = pos.turn
    for m in gen_pseudo(pos):
        np = make_move(pos, m)
        ksq = find_king(np.board, mover)
        if ksq is None or not is_attacked(np.board, ksq, np.turn):
            out.append(m)
    return out


def insufficient_material(board):
    minors = []
    for sq, p in enumerate(board):
        u = p.upper()
        if u in ('P', 'R', 'Q'):
            return False
        if u in ('B', 'N'):
            minors.append((p, sq))
    if len(minors) <= 1:
        return True
    if len(minors) == 2:
        (p1, s1), (p2, s2) = minors
        if p1.upper() == 'B' and p2.upper() == 'B' and color_of(p1) != color_of(p2):
            # bishops on same-coloured squares -> dead draw
            return (s1 // 8 + s1 % 8) % 2 == (s2 // 8 + s2 % 8) % 2
    return False


def to_san(pos, move, legal=None):
    src, dst, promo = move
    b = pos.board
    piece = b[src]
    kind = piece.upper()

    if kind == 'K' and abs(dst % 8 - src % 8) == 2:
        text = 'O-O' if dst % 8 == 6 else 'O-O-O'
    else:
        capture = b[dst] != '.' or (kind == 'P' and dst == pos.ep)
        if kind == 'P':
            text = (FILES[src % 8] + 'x') if capture else ''
            text += sq_name(dst)
            if promo:
                text += '=' + promo
        else:
            if legal is None:
                legal = legal_moves(pos)
            rivals = [m for m in legal
                      if m[1] == dst and m[0] != src and b[m[0]] == piece]
            disamb = ''
            if rivals:
                if not any(m[0] % 8 == src % 8 for m in rivals):
                    disamb = FILES[src % 8]
                elif not any(m[0] // 8 == src // 8 for m in rivals):
                    disamb = RANKS[src // 8]
                else:
                    disamb = sq_name(src)
            text = kind + disamb + ('x' if capture else '') + sq_name(dst)

    nxt = make_move(pos, move)
    if in_check(nxt):
        text += '#' if not legal_moves(nxt) else '+'
    return text


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

SQ = 72
MARGIN = 18
BOARD_PX = SQ * 8 + MARGIN * 2

LIGHT = "#EEEED2"
DARK = "#769656"
LIGHT_LAST = "#F6F islandsEB"  # placeholder replaced below
LIGHT_LAST = "#F7EC74"
DARK_LAST = "#DAC431"
LIGHT_SEL = "#F9F97A"
DARK_SEL = "#BBCB2B"
CHECK_COLOR = "#E06666"
DOT = "#00000055"
BG = "#312E2B"
PANEL = "#3C3936"
TEXT = "#EDEBE9"

WHITE_FILL = "#FFFFFF"
BLACK_FILL = "#1B1A19"
OUTLINE = "#111111"


class ChessGUI:
    def __init__(self, root):
        self.root = root
        root.title("Chess")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.piece_family = self._pick_font()
        self.piece_font = tkfont.Font(family=self.piece_family, size=int(SQ * 0.62))
        self.coord_font = tkfont.Font(family="Helvetica", size=9, weight="bold")

        wrap = tk.Frame(root, bg=BG)
        wrap.pack(padx=10, pady=10)

        self.canvas = tk.Canvas(wrap, width=BOARD_PX, height=BOARD_PX,
                                bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0)
        self.canvas.bind("<Button-1>", self.on_click)

        side = tk.Frame(wrap, bg=PANEL)
        side.grid(row=0, column=1, sticky="ns", padx=(10, 0))

        self.status = tk.Label(side, text="", bg=PANEL, fg=TEXT,
                               font=("Helvetica", 13, "bold"),
                               width=24, pady=10, wraplength=200)
        self.status.pack(fill=tk.X)

        listwrap = tk.Frame(side, bg=PANEL)
        listwrap.pack(fill=tk.BOTH, expand=True, padx=8)
        scroll = tk.Scrollbar(listwrap)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.movelist = tk.Listbox(listwrap, width=22, height=18,
                                   bg="#2B2926", fg=TEXT, borderwidth=0,
                                   highlightthickness=0, activestyle="none",
                                   font=("Courier", 11),
                                   yscrollcommand=scroll.set)
        self.movelist.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.movelist.yview)

        btns = tk.Frame(side, bg=PANEL)
        btns.pack(fill=tk.X, pady=10, padx=8)
        for label, cmd in (("New game", self.new_game),
                           ("Undo", self.undo),
                           ("Flip board", self.flip)):
            tk.Button(btns, text=label, command=cmd, width=20,
                      relief=tk.FLAT, bg="#4E4A46", fg=TEXT,
                      activebackground="#615C57", activeforeground=TEXT,
                      pady=4).pack(pady=2)

        root.bind("<Control-z>", lambda e: self.undo())
        root.bind("<Control-n>", lambda e: self.new_game())

        self.flipped = False
        self.new_game()

    def _pick_font(self):
        available = set(tkfont.families())
        for name in ("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS",
                     "Apple Symbols", "Noto Sans Symbols 2", "FreeSerif",
                     "Symbola"):
            if name in available:
                return name
        return "Helvetica"

    # ---------------- state ----------------

    def new_game(self):
        self.pos = Position.start()
        self.stack = []            # previous positions, for undo
        self.sans = []             # SAN strings
        self.keys = [self.pos.key()]
        self.last_move = None
        self.selected = None
        self.over = False
        self.legal = legal_moves(self.pos)
        self.movelist.delete(0, tk.END)
        self.draw()
        self.update_status()

    def undo(self):
        if not self.stack:
            return
        self.pos = self.stack.pop()
        self.sans.pop()
        self.keys.pop()
        self.last_move = None
        self.selected = None
        self.over = False
        self.legal = legal_moves(self.pos)
        self.refresh_movelist()
        self.draw()
        self.update_status()

    def flip(self):
        self.flipped = not self.flipped
        self.draw()

    # ---------------- geometry ----------------

    def screen_rc(self, r, c):
        return (7 - r, 7 - c) if self.flipped else (r, c)

    def top_left(self, r, c):
        sr, sc = self.screen_rc(r, c)
        return MARGIN + sc * SQ, MARGIN + sr * SQ

    def square_at(self, x, y):
        sc = (x - MARGIN) // SQ
        sr = (y - MARGIN) // SQ
        if not (0 <= sr < 8 and 0 <= sc < 8):
            return None
        r, c = (7 - sr, 7 - sc) if self.flipped else (sr, sc)
        return int(r) * 8 + int(c)

    # ---------------- drawing ----------------

    def draw(self):
        cv = self.canvas
        cv.delete("all")
        cv.create_rectangle(0, 0, BOARD_PX, BOARD_PX, fill=BG, outline="")

        check_sq = None
        if in_check(self.pos):
            check_sq = find_king(self.pos.board, self.pos.turn)

        targets = {}
        if self.selected is not None:
            for m in self.legal:
                if m[0] == self.selected:
                    targets[m[1]] = self.pos.board[m[1]] != '.' or (
                        self.pos.board[m[0]].upper() == 'P' and m[1] == self.pos.ep)

        for r in range(8):
            for c in range(8):
                sq = r * 8 + c
                x, y = self.top_left(r, c)
                light = (r + c) % 2 == 0
                fill = LIGHT if light else DARK
                if self.last_move and sq in self.last_move[:2]:
                    fill = LIGHT_LAST if light else DARK_LAST
                if sq == self.selected:
                    fill = LIGHT_SEL if light else DARK_SEL
                if sq == check_sq:
                    fill = CHECK_COLOR
                cv.create_rectangle(x, y, x + SQ, y + SQ, fill=fill, outline="")

                if sq in targets:
                    if targets[sq]:
                        cv.create_oval(x + 4, y + 4, x + SQ - 4, y + SQ - 4,
                                       outline="#2F2F2F", width=4)
                    else:
                        m = SQ * 0.36
                        cv.create_oval(x + m, y + m, x + SQ - m, y + SQ - m,
                                       fill="#5A5A5A", outline="")

                piece = self.pos.board[sq]
                if piece != '.':
                    self.draw_piece(x + SQ / 2, y + SQ / 2, piece)

        # coordinates in the margins
        for i in range(8):
            r, c = (7 - i, i) if not self.flipped else (i, 7 - i)
            fx = MARGIN + (i if not self.flipped else 7 - i) * SQ + SQ / 2
            cv.create_text(fx, BOARD_PX - MARGIN / 2, text=FILES[i],
                           fill=TEXT, font=self.coord_font)
            ry = MARGIN + (i if not self.flipped else 7 - i) * SQ + SQ / 2
            cv.create_text(MARGIN / 2, ry, text=RANKS[i],
                           fill=TEXT, font=self.coord_font)

    def draw_piece(self, cx, cy, piece):
        glyph = GLYPH[piece.upper()]
        fill = WHITE_FILL if piece.isupper() else BLACK_FILL
        # fake an outline by stamping the glyph around the centre
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)):
            self.canvas.create_text(cx + dx, cy + dy, text=glyph,
                                    font=self.piece_font, fill=OUTLINE)
        self.canvas.create_text(cx, cy, text=glyph,
                                font=self.piece_font, fill=fill)

    def refresh_movelist(self):
        self.movelist.delete(0, tk.END)
        for i in range(0, len(self.sans), 2):
            num = i // 2 + 1
            white = self.sans[i]
            black = self.sans[i + 1] if i + 1 < len(self.sans) else ""
            self.movelist.insert(tk.END, f"{num:>3}. {white:<8}{black}")
        self.movelist.yview_moveto(1.0)

    def update_status(self):
        if self.over:
            return
        side = "White" if self.pos.turn == 'w' else "Black"
        msg = f"{side} to move"
        if in_check(self.pos):
            msg += " — check!"
        self.status.config(text=msg)

    # ---------------- interaction ----------------

    def on_click(self, event):
        if self.over:
            return
        sq = self.square_at(event.x, event.y)
        if sq is None:
            return
        piece = self.pos.board[sq]

        if self.selected is not None:
            candidates = [m for m in self.legal
                          if m[0] == self.selected and m[1] == sq]
            if candidates:
                move = candidates[0]
                if len(candidates) > 1:      # promotion
                    choice = self.ask_promotion(self.pos.turn)
                    move = next(m for m in candidates if m[2] == choice)
                self.play(move)
                return
            if color_of(piece) == self.pos.turn:
                self.selected = sq
            else:
                self.selected = None
            self.draw()
            return

        if color_of(piece) == self.pos.turn:
            self.selected = sq
            self.draw()

    def play(self, move):
        self.sans.append(to_san(self.pos, move, self.legal))
        self.stack.append(self.pos)
        self.pos = make_move(self.pos, move)
        self.keys.append(self.pos.key())
        self.last_move = move
        self.selected = None
        self.legal = legal_moves(self.pos)
        self.refresh_movelist()
        self.draw()
        self.update_status()
        self.check_end()

    def check_end(self):
        result = None
        if not self.legal:
            if in_check(self.pos):
                winner = "Black" if self.pos.turn == 'w' else "White"
                result = f"Checkmate — {winner} wins."
            else:
                result = "Stalemate — draw."
        elif self.pos.halfmove >= 100:
            result = "Draw by the fifty-move rule."
        elif insufficient_material(self.pos.board):
            result = "Draw — insufficient material."
        elif self.keys.count(self.pos.key()) >= 3:
            result = "Draw by threefold repetition."

        if result:
            self.over = True
            self.status.config(text=result)
            self.root.after(60, lambda: messagebox.showinfo("Game over", result))

    def ask_promotion(self, color):
        dlg = tk.Toplevel(self.root)
        dlg.title("Promote to")
        dlg.configure(bg=PANEL)
        dlg.resizable(False, False)
        dlg.transient(self.root)
        picked = {'v': 'Q'}

        def choose(k):
            picked['v'] = k
            dlg.destroy()

        row = tk.Frame(dlg, bg=PANEL)
        row.pack(padx=10, pady=10)
        for k in ('Q', 'R', 'B', 'N'):
            tk.Button(row, text=GLYPH[k], width=2,
                      font=(self.piece_family, 26),
                      fg=BLACK_FILL if color == 'b' else "#444444",
                      bg="#D8D4CE", relief=tk.FLAT,
                      command=lambda k=k: choose(k)).pack(side=tk.LEFT, padx=3)

        dlg.protocol("WM_DELETE_WINDOW", lambda: choose('Q'))
        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        dlg.grab_set()
        self.root.wait_window(dlg)
        return picked['v']


def main():
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
