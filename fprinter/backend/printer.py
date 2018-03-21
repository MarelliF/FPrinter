from . import constants
from .svg_slice_lib import parse_svg
import json

import pyglet
import io
import cairosvg
import xml
import time
import shutil
import os
from PIL import Image


class Printer():
    def __init__(self, window):
        self.reset()
        self.window = window

    def reset(self, purge=True):
        if purge:
            self.layers = []
            self.name = ''

        self.printing_in_progress = False
        self.is_paused = False
        self.current_layer = -1
        self.layer_timestamp = -1
        self.paused_exposition = 0

        self.save_status()

        if os.path.exists(constants.LAYER_PNG):
            os.remove(constants.LAYER_PNG)

    def save_status(self):
        status = {'in_progress': self.printing_in_progress, 'paused': self.is_paused,
                  'name': self.name, 'current_layer': self.current_layer + 1,
                  'max_layer': len(self.layers)}

        with open(constants.PRINTER_STATUS, 'w') as file:
            json.dump(status, file)

    def load_svg(self):
        self.layers = parse_svg(constants.SVG_FILE)
        with open(constants.SVG_NAME, 'r') as file:
            self.name = file.read()
        self.save_status()

    def start(self):
        if len(self.layers) is 0:
            # return error code if the layers are not loaded
            print('WARNING: tried to start printing with no layers loaded')
            return 1

        elif self.printing_in_progress:
            print('WARNING: tried to start printing while already running')
            return 2

        else:
            print('INFO: starting to print - {}'.format(self.name))
            self.printing_in_progress = True
            self.is_paused = False
            self.current_layer = -1

            self.save_status()

            # TODO start the printing process

            return 0

    def pause(self):
        if not self.printing_in_progress:
            print('WARNING: tried to pause while not printing')
            return 1

        elif self.is_paused:
            print('WARNING: tried to pause while already paused')
            return 2

        else:
            self.window.clear()
            timestamp = time.time()
            self.is_paused = True
            self.save_status()
            self.paused_exposition = timestamp - self.layer_timestamp

            print('INFO: print paused')
            return 0

    def resume(self):
        if not self.printing_in_progress:
            print('WARNING: tried to resume while not printing')
            return 1

        elif not self.is_paused:
            print('WARNING: tried to resume while already running')
            return 2

        else:
            self.is_paused = False
            self.save_status()
            self.project_layer()
            self.layer_timestamp -= self.paused_exposition

            print('INFO: print resumed')
            return 0

    def abort(self):
        self.window.clear()
        self.reset()

        self.save_status()

        # TODO abort printing
        print('INFO: aborting print')

    def end(self):
        self.window.clear()
        self.reset(purge=False)

        self.save_status()
        pass

    def update(self):
        if self.printing_in_progress and not self.is_paused:

            if time.time() - self.layer_timestamp > constants.EXPOSITION_TIME:

                self.current_layer += 1

                if self.current_layer >= len(self.layers):
                    self.end()
                    print('INFO: print finished')

                else:
                    self.project_layer()
                    self.save_status()
                    # TODO print a new layer

    def project_layer(self):
        layer = self.layers[self.current_layer]

        stream = io.BytesIO()
        cairosvg.surface.PNGSurface.convert(
            bytestring=xml.etree.ElementTree.tostring(layer),
            write_to=stream, dpi=96, scale=1)
        image = pyglet.image.load('', file=stream)
        stream.close()

        self.window.clear()
        image.blit(x=(self.window.width - image.width) // 2,
            y=(self.window.height - image.height) // 2)
        self.layer_timestamp = time.time()

        temp_file = constants.LAYER_PNG + '~'

        buffer = pyglet.image.get_buffer_manager().get_color_buffer()
        b_image = buffer.image_data.get_image_data()
        pil_image = Image.frombytes(b_image.format, (b_image.width, b_image.height),
            b_image.get_data(b_image.format, b_image.pitch))
        pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
        pil_image = pil_image.convert('RGB')
        pil_image.save(temp_file, 'PNG')

        os.rename(temp_file, constants.LAYER_PNG)
