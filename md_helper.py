from rich.console import Console
from rich.markdown import Markdown

class md:
    def __init__(self):
        self._console = Console(markup=False)
    def print(self, msg):
        self._console.print(Markdown(msg))
