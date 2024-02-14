from random import randint

class GameLogic:

    DIE = 6
    POINTS = 24
    CHECKERS_STARTING_POS = ((6, 5), (8, 3), (13, 5), (24, 2))

    def __init__(self):
        self.points = self.set_starting_checkers()
        self.bar = []
        self.scores = [0, 0]

    def set_starting_checkers(self):
        """Sets the checker's starting position."""
        points = [[] for i in range(self.POINTS)]

        for player in (0, 1): # 0 host player, 1 guest player
            for pos, n in self.CHECKERS_STARTING_POS:
                for _ in range(n):
                    points[
                        abs(-((self.POINTS - 1) * player) + pos - 1)
                    ].append(player)
        
        return points

    def throw_dice(self):
        return randint(1, self.DIE), randint(1, self.DIE)

    def is_point_open(self, points, point, player):
        opponent = 0 if player == 1 else 1
        return len([c for c in points[point] if c == opponent]) < 2

    def get_possible_moves(self, state, point, player, dice):
        points, bar, scores = state
        moves = []

        if not player in bar:
            curr_point = points[point - 1]
            point_index = point
        else:
            curr_point = [player]
            point_index = 25

        if player in curr_point:
            for val in dice:
                possible_point = point_index - 1 - val
                if not 0 <= possible_point <= 23:
                    continue
                if self.is_point_open(points, possible_point, player):
                    moves.append(possible_point + 1)
                
        return moves

    def move_to(self, points, bar, scores, point, to, player):
        opponent = 0 if player == 1 else 1
        if point != 0:
            take_from = points[point - 1]
            index = -1
            move = point - to
        else:
            take_from = bar
            index = bar.index(player)
            move = 25 - to

        take_from.pop(index)
        if opponent in points[to - 1]:
            points[to - 1].pop()
            bar.append(opponent)
        points[to - 1].append(player)  

        return points, bar, scores, move

    def get_possible_bearoffs(self, points, draw, player):
        n = len(points) // 4
        bearoffs = []
        for d in sorted(draw, reverse=True):
            for i, point in enumerate(points[n-1::-1]):
                index = n - i
                if player in point and index <= d:
                    bearoffs.append((index - 1, d))
                    break

        return bearoffs

    def bearoff(self, points, bar, scores, point, player):
        scores[player] += 1
        points[point - 1].pop()
        return points, bar, scores

    def check_for_bearoff(self, points, bar, scores, player):
        return not any(player in point for point in points[6:])

    def check_for_winner(self, score):
        return score == 1

    def show_board(self):
        top_row = self.points[self.POINTS//2:]
        bottom_row = self.points[:self.POINTS//2]

        for i in range(5):
            for p in top_row:
                if len(p) > i:
                    print(p[i], end=" ")
                else:
                    print("|", end=" ")
            print()
        print()
        for i in range(4, -1, -1):
            for p in reversed(bottom_row):
                if len(p) > i:
                    print(p[i], end=" ")
                else:
                    print("|", end=" ")
            print()
        print()

    def get_state(self):
        return self.points, self.bar, self.scores


if __name__ == "__main__":
    game = GameLogic()
    game.show_board()
    