#!/usr/bin/python3

from src.app import App
from src.controller import Controller

if __name__ == "__main__":
    controller = Controller()
    app = App(controller)
    app.mainloop()
