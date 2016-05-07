# -*- coding: utf-8 -*-
import os

from slugify import slugify
import datetime
import settings


# Small utility class that prints in stdio and
class Printer(object):

    def __init__(self, filename, configuration, print_in_stdio=True):
        self.filename = filename
        self.configuration = configuration
        self.string = u""
        self.print_in_stdio = print_in_stdio

    def p(self, text):
        if self.print_in_stdio:
            print(text)
        self.string += text + u"\n"

    def newline(self):
        self.p(u"\n")

    def flush(self):
        now_str = datetime.datetime.now(settings.TIMEZONE).strftime("%Y_%m_%d_%H_%M_%S")
        output_directory = self.configuration.output_dir
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        output_filename = u"{0}/{1}-{2}.txt".format(output_directory, slugify(self.filename), now_str)
        with open(output_filename, "w") as output_file:
            output_file.write(self.string.encode('utf8'))