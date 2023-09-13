import numpy as np
import tkinter as tk
from functools import partial

class Board:
    def __init__(self):
        # flip MSB for white = 0 black = 1
        # pawn = 0b001, rook = 0b010, knight = 0b011, bishop = 0b100, queen = 0b101, king = 0b110, 0 = empty square
        self.state = np.zeros((8, 8))
        self.buttonray = np.zeros((8,8), dtype=object)
        self.buttonrayclone = np.zeros((8, 8), dtype=object)
        self.state = self.state.astype(int)
        self.turn = 0
        self.whiteking = [7, 4]
        self.blacking = [0, 4]
        self.cflag = 0
        self.movestore = []
        self.takenpiece = None
        self.latch = 0
        self.kingmove = [False, False]
        self.rook = [False, False, False, False]
        self.emptysquare = [False, False, False, False, False, False, False, False, False, False]
        self.enpassant = np.zeros((8, 8), dtype=int)
        # pawn setup
        for i in range(8):
            self.state[1, i] = 0b1001
            self.state[6, i] = 0b0001

        # black pieces
        self.state[0, 0] = 0b1010
        self.state[0, 1] = 0b1011
        self.state[0, 2] = 0b1100
        self.state[0, 3] = 0b1101
        self.state[0, 4] = 0b1110
        self.state[0, 5] = 0b1100
        self.state[0, 6] = 0b1011
        self.state[0, 7] = 0b1010
        #white pieces
        self.state[7, 0] = 0b0010
        self.state[7, 1] = 0b0011
        self.state[7, 2] = 0b0100
        self.state[7, 3] = 0b0101
        self.state[7, 4] = 0b0110
        self.state[7, 5] = 0b0100
        self.state[7, 6] = 0b0011
        self.state[7, 7] = 0b0010

        win = tk.Tk()
        self.Button_ID = []
        self.Boarddict = {}
        self.Boarddict["99"] = tk.PhotoImage(file=r"0.png")

        for i in range(8):
            for j in range(8):
                if (i + j) % 2 == 0:
                    colour = "#FFBEB0"
                else:
                    colour = "#A64A36"
                strinky = ("{}{}".format(i, j))
                self.Boarddict[strinky] = tk.PhotoImage(file=r"{}.png".format(self.state[i, j]))
                win.B = tk.Button(bg=colour, activebackground="lawn green", image=self.Boarddict[strinky],
                                   height=60, width=60, command=partial(self.move, (i, j)))
                win.B.grid(row=i, column=j)
                self.Button_ID.append(win.B)
                self.buttonray[i, j] = win.B
                self.buttonrayclone[i, j] = win.B

        win.mainloop()

    def legal_list(self, row, col, norecurse):
        knight = False
        moves = []
        if self.state[row, col] & 0b0111 == 0b0010: #rook
            identity = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        elif self.state[row, col] & 0b0111 == 0b0100: #bishop
            identity = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        elif self.state[row, col] & 0b0111 == 0b0101: #queen
            identity = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
        elif self.state[row, col] & 0b0111 == 0b0011: #knight
            knight = True
            identity = [(2, 1), (2, -1), (1, 2), (1, -2), (-2, 1), (-1, 2), (-1, -2), (-2, -1)]
        elif self.state[row, col] == 0b0110: #Whiteking
            knight = True
            identity = [(1, 1), (1, 0), (0, 1), (1, -1), (-1, 1), (-1, 0), (0, -1), (-1, -1)]
            if not self.kingmove[1] and not self.rook[2] and self.emptysquare[5] and self.emptysquare[6] and self.emptysquare[7]:
                identity.append((0, -2))
            if not self.kingmove[1] and not self.rook[3] and self.emptysquare[8] and self.emptysquare[9]:
                identity.append((0, 2))
        elif self.state[row, col] == 0b1110: #Blackking
            knight = True
            identity = [(1, 1), (1, 0), (0, 1), (1, -1), (-1, 1), (-1, 0), (0, -1), (-1, -1)]
            if not self.kingmove[0] and not self.rook[0] and self.emptysquare[0] and self.emptysquare[1] and self.emptysquare[2]:
                identity.append((0, -2))
            if not self.kingmove[0] and not self.rook[1] and self.emptysquare[3] and self.emptysquare[4]:
                identity.append((0, 2))
        elif self.state[row, col] == 0b0001: #white pawn
            if row == 6:
                identity = [(-1, 0), (-2, 0)]
                if self.state[row-2, col] != 0:
                    identity = [(-1, 0)]
                elif self.state[(row-1, col)]:
                    identity = []
            else:
                identity = [(-1, 0)]
                if self.state[row-1, col] != 0:
                    identity = []
            if self.state[row-1, col-1] != 0 or self.enpassant[row-1, col-1] == 1:
                identity.append((-1, -1))
            if col+1 < 8 and (self.state[row-1, col+1] != 0 or self.enpassant[row-1, col+1]):
                identity.append((-1, 1))
            knight = True
        elif self.state[row, col] == 0b1001: #black pawn
            if row == 1:
                identity = [(1, 0), (2, 0)]
                if self.state[row + 2, col] != 0:
                    identity = [(1, 0)]
                elif self.state[(row + 1, col)]:
                    identity = []
            else:
                identity = [(1, 0)]
                if row+1 < 8 and self.state[row+1, col] != 0:
                    identity = []
            if row+1 < 8 and (self.state[row+1, col-1] != 0 or self.enpassant[row+1, col-1] == 1):
                identity.append((1, -1))
            if row+1 < 8 and col+1 < 8 and (self.state[row+1, col+1] != 0 or self.enpassant[row+1, col+1] == 1):
                identity.append((1, 1))
            knight = True
        else:
            identity = []
        if norecurse:
            for i in range(len(identity)):
                n = identity[i][0]
                m = identity[i][1]
                check = True
                while check:
                    if row+n > 7 or col+m > 7 or row+n < 0 or col+m < 0:
                        check = False
                    elif self.state[row+n,col+m] == 0:
                        moves.append((row+n, col+m))
                    elif (self.state[row+n,col+m] ^ self.state[row, col]) >> 3 == 1:
                        moves.append((row+n, col+m))
                        check = False
                    else:
                        check = False
                    n += identity[i][0]
                    m += identity[i][1]
                    if knight:
                        check = False
        else:
            for i in range(len(identity)):
                n = identity[i][0]
                m = identity[i][1]
                check = True
                while check:
                    if row + n > 7 or col + m > 7 or row + n < 0 or col + m < 0:
                        check = False
                    elif self.state[row + n, col + m] == 0:
                        self.dummymove((row, col), (row+n, col+m), False)
                        if not self.in_check():
                            moves.append((row + n, col + m))
                        self.dummymove((row, col), (row + n, col + m), True)
                    elif (self.state[row + n, col + m] ^ self.state[row, col]) >> 3 == 1:
                        self.dummymove((row, col), (row + n, col + m), False)
                        if not self.in_check():
                            moves.append((row + n, col + m))
                        self.dummymove((row, col), (row + n, col + m), True)
                        check = False
                    else:
                        check = False
                    n += identity[i][0]
                    m += identity[i][1]
                    if knight:
                        check = False
        return moves

    def in_check(self, square=(9, 9)):
        if square == (9, 9):
            if self.turn%2 == 0:
                kingsquare = self.whiteking
                colorsquare = self.whiteking
            else:
                kingsquare = self.blacking
                colorsquare = self.blacking
        else:
            if self.turn%2 ==0:
                colorsquare = self.whiteking
            else:
                colorsquare = self.blacking
            kingsquare = square

        for i in range(8):
            for j in range(8):
                if (self.state[i, j] ^ self.state[colorsquare[0], colorsquare[1]]) >> 3 == 1 and self.state[i, j] != 0:
                    legalmoves = self.legal_list(i, j, True)
                    if (kingsquare[0], kingsquare[1]) in legalmoves:
                        self.cflag += 1
        if self.cflag > 0:
            self.cflag = 0
            return True
        else:
            self.cflag = 0
            return False



    def move(self, c):
        bname = self.buttonray[c]
        self.movestore.append(bname)
        if len(self.movestore) == 2:
            info1 = self.movestore[0].grid_info()
            info2 = self.movestore[1].grid_info()
            piece = (info1["row"], info1["column"])
            square = (info2["row"], info2["column"])
            moves = self.legal_list(piece[0], piece[1], False)
            if square in moves and (self.state[piece] >= 9 and self.turn % 2 == 1 or self.state[piece] < 9 and self.turn % 2 == 0):

                if (info1["row"] + info1["column"]) % 2 == 0:
                    self.movestore[1].config(bg="#FFBEB0", image=self.Boarddict["99"])
                else:
                    self.movestore[1].config(bg="#A64A36", image=self.Boarddict["99"])

                if (info2["row"] + info2["column"]) % 2 == 0:
                    self.movestore[0].config(bg="#FFBEB0")
                else:
                    self.movestore[0].config(bg="#A64A36")
                self.movestore[0].grid(row=info2["row"], column=info2["column"])
                self.movestore[1].grid(row=info1["row"], column=info1["column"])
                if self.state[piece] == 0b0001 and self.state[square] == 0 and (abs(piece[0] - square[0]), abs(piece[1] - square[1])) == (1, 1):
                    self.buttonrayclone[square[0]+1, square[1]].config(image=self.Boarddict["99"])
                    self.state[square[0]+1, square[1]] = 0
                if self.state[piece] == 0b1001 and self.state[square] == 0 and (abs(piece[0] - square[0]), abs(piece[1] - square[1])) == (1, 1):
                    self.buttonrayclone[square[0]-1, square[1]].config(image=self.Boarddict["99"])
                    self.state[square[0]-1, square[1]] = 0
                self.state[square] = self.state[piece]
                self.state[piece] = 0
                self.turn += 1
                if piece[0] == self.whiteking[0] and piece[1] == self.whiteking[1]:
                    self.whiteking[0] = square[0]
                    self.whiteking[1] = square[1]
                    self.kingmove[1] = True
                if piece[0] == self.blacking[0] and piece[1] == self.blacking[1]:
                    self.blacking[0] = square[0]
                    self.blacking[1] = square[1]
                    self.kingmove[0] = True
                self.castle(piece)
                if self.state[square] == 0b0110 and abs(piece[1]-square[1]) == 2 and square == (7, 2):
                    self.buttonrayclone[7, 0].config(bg="#FFBEB0", image=self.Boarddict["70"])
                    self.buttonrayclone[7, 3].config(bg="#A64A36", image=self.Boarddict["99"])
                    self.buttonrayclone[7, 0].grid(row=7, column=3)
                    self.buttonrayclone[7, 3].grid(row=7, column=0)
                    self.state[7, 3] = 0b0010
                    self.state[7, 0] = 0b0000
                if self.state[square] == 0b0110 and abs(piece[1]-square[1]) == 2 and square == (7, 6):
                    self.buttonrayclone[7, 7].config(bg="#FFBEB0", image=self.Boarddict["70"])
                    self.buttonrayclone[7, 5].config(bg="#FFBEB0", image=self.Boarddict["99"])
                    self.buttonrayclone[7, 7].grid(row=7, column=5)
                    self.buttonrayclone[7, 5].grid(row=7, column=7)
                    self.state[7, 5] = 0b0010
                    self.state[7, 7] = 0b0000
                if self.state[square] == 0b1110 and abs(piece[1]-square[1]) == 2 and square == (0, 2):
                    self.buttonrayclone[0, 0].config(bg="#A64A36", image=self.Boarddict["00"])
                    self.buttonrayclone[0, 3].config(bg="#FFBEB0", image=self.Boarddict["99"])
                    self.buttonrayclone[0, 0].grid(row=0, column=3)
                    self.buttonrayclone[0, 3].grid(row=0, column=0)
                    self.state[0, 3] = 0b1010
                    self.state[0, 0] = 0b0000
                if self.state[square] == 0b1110 and abs(piece[1]-square[1]) == 2 and square == (0, 6):
                    self.buttonrayclone[0, 7].config(bg="#A64A36", image=self.Boarddict["00"])
                    self.buttonrayclone[0, 5].config(bg="#A64A36", image=self.Boarddict["99"])
                    self.buttonrayclone[0, 7].grid(row=0, column=5)
                    self.buttonrayclone[0, 5].grid(row=0, column=7)
                    self.state[0, 5] = 0b1010
                    self.state[0, 7] = 0b0000
                for i in range(8):
                    self.enpassant[2, i] = 0
                    self.enpassant[5, i] = 0
                if self.state[square] & 0b0111 == 0b0001 and (piece[0] == 1 or piece[0] == 6):
                    if piece[0] == 1 and self.state[square] == 0b1001:
                        self.enpassant[piece[0]+1, piece[1]] = 1
                    if piece[0] == 6 and self.state[square] == 0b0001:
                        self.enpassant[piece[0]-1, piece[1]] = 1
                if self.checkmate():
                    print("Checkmate!")
                store = self.buttonrayclone[piece]
                self.buttonrayclone[piece] = self.buttonrayclone[square]
                self.buttonrayclone[square] = store
                if self.state[square] & 0b0111 == 0b0001 and (square[0] == 0 or square[0] == 7):
                    self.promote(square)
            self.movestore.clear()

    def castle(self, piece):
        if self.state[piece] == 0b0010 and piece == (7, 0):
            self.rook[2] = True
        if self.state[piece] == 0b0010 and piece == (7, 7):
            self.rook[3] = True
        if self.state[piece] == 0b1010 and piece == (0, 0):
            self.rook[0] = True
        if self.state[piece] == 0b1010 and piece == (7, 7):
            self.rook[1] = True
        if self.state[0, 1] != 0 or self.in_check((0, 1)):
            self.emptysquare[0] = False
        else:
            self.emptysquare[0] = True
        if self.state[0, 2] != 0 or self.in_check((0, 2)):
            self.emptysquare[1] = False
        else:
            self.emptysquare[1] = True
        if self.state[0, 3] != 0 or self.in_check((0, 3)):
            self.emptysquare[2] = False
        else:
            self.emptysquare[2] = True
        if self.state[0, 5] != 0 or self.in_check((0, 5)):
            self.emptysquare[3] = False
        else:
            self.emptysquare[3] = True
        if self.state[0, 6] != 0 or self.in_check((0, 6)):
            self.emptysquare[4] = False
        else:
            self.emptysquare[4] = True
        if self.state[7, 1] != 0 or self.in_check((7, 1)):
            self.emptysquare[5] = False
        else:
            self.emptysquare[5] = True
        if self.state[7, 2] != 0 or self.in_check((7, 2)):
            self.emptysquare[6] = False
        else:
            self.emptysquare[6] = True
        if self.state[7, 3] != 0 or self.in_check((7, 3)):
            self.emptysquare[7] = False
        else:
            self.emptysquare[7] = True
        if self.state[7, 5] != 0 or self.in_check((7, 5)):
            self.emptysquare[8] = False
        else:
            self.emptysquare[8] = True
        if self.state[7, 6] != 0 or self.in_check((7, 6)):
            self.emptysquare[9] = False
        else:
            self.emptysquare[9] = True

    def checkmate(self):
        if self.turn%2 == 0:
            kingsquare = self.whiteking
        else:
            kingsquare = self.blacking
        for i in range(8):
            for j in range(8):
                if (self.state[i, j] ^ self.state[kingsquare[0], kingsquare[1]]) >> 3 == 1 and self.state[i, j] != 0:
                    moves = self.legal_list(i, j, False)
                    if moves != []:
                        return False
        return True

    def promote(self, square):
        if square[0] == 0:
            self.state[0, square[1]] = 0b0101
            self.buttonrayclone[0, square[1]].config(image=self.Boarddict["73"])
        if square[0] == 7:
            self.state[7, square[1]] = 0b1101
            self.buttonrayclone[7, square[1]].config(image=self.Boarddict["03"])

    def dummymove(self, piece, square, undo):
        if piece == square:
            return
        if not undo:
            if self.state[piece] >= 9 and self.turn % 2 == 1 or self.state[piece] < 9 and self.turn % 2 == 0:
                self.latch = 0
                self.takenpiece = self.state[square]
                self.state[square] = self.state[piece]
                self.state[piece] = 0
                if piece[0] == self.whiteking[0] and piece[1] == self.whiteking[1]:
                    self.whiteking[0] = square[0]
                    self.whiteking[1] = square[1]
                if piece[0] == self.blacking[0] and piece[1] == self.blacking[1]:
                    self.blacking[0] = square[0]
                    self.blacking[1] = square[1]
            else:
                self.latch = 1

        elif self.latch == 0:
            self.state[piece] = self.state[square]
            self.state[square] = self.takenpiece
            if square[0] == self.whiteking[0] and square[1] == self.whiteking[1]:
                self.whiteking[0] = piece[0]
                self.whiteking[1] = piece[1]
            if square[0] == self.blacking[0] and square[1] == self.blacking[1]:
                self.blacking[0] = piece[0]
                self.blacking[1] = piece[1]


game = Board()

