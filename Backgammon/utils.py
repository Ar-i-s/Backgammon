import pickle
import pygame
from pygame import mouse

class Mouse:
    """A class to handle mouse inputs independently from the game window size."""
    def __init__(self, base_res, render_res):
        self.base_res = base_res
        self.render_res = render_res

    def scale(self, pos):
        """Scales a (x, y) position based on base_res and render_res."""
        scaledx = self._map_to(pos[0], 0, self.render_res[0], 0, self.base_res[0])
        scaledy = self._map_to(pos[1], 0, self.render_res[1], 0, self.base_res[1])
        return scaledx, scaledy

    def _map_to(self, x, minx, maxx, a, b):
        """Maps x value (ranging from minx to maxx) to range (a, b)."""
        return (b - a) * (x - minx) / (maxx - minx) + a

    def get_pos(self):
        """Returns the scaled mouse position."""
        relative_pos = mouse.get_pos()
        absolute_pos = self.scale(relative_pos)
        return absolute_pos
    
    def get_click(self):
        """Returns wether the mouse left button is being pressed."""
        return mouse.get_pressed()[0]

    def set_pointing_cursor(self, pointing):
        """Sets pointing or normal cursor based on given boolean."""
        if pointing:
            mouse.set_system_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)

class Serialization:
    """A class to handle serialization of the game state."""
    @staticmethod
    def list_to_bytes(data):
        """Serializes a given list to bytes data."""
        serialized = pickle.dumps(data)
        return serialized, len(serialized)

    @staticmethod
    def bytes_to_list(data):
        """Deserializes given bytes to a list."""
        return pickle.loads(data)

