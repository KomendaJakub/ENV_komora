#!/usr/bin/python3
import os.path


from src.app import App
from src.controller import Controller


if __name__ == "__main__":
    DIR_PATH = os.path.dirname(__file__)
    os.chdir(DIR_PATH)
    controller = Controller()
    app = App(controller)
    app.mainloop()
