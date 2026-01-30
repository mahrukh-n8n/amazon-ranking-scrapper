import sys
import asyncio
import qasync
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    # Create QApplication
    app = QApplication(sys.argv)

    # Event Loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Main Window
    window = MainWindow()
    window.show()

    # Run the event loop
    with loop:
        # qasync.QEventLoop.run_forever() is called by run_until_complete if we pass a future
        # or we can use loop.run_forever()
        # The recommended way for qasync is usually just loop.run_forever()
        # But we are inside an async def, so we are already 'running'.
        # Actually, standard pattern with qasync is:
        # loop = qasync.QEventLoop(app)
        # asyncio.set_event_loop(loop)
        # with loop:
        #    loop.run_until_complete(main_coroutine())

        # Since we are already in main_coroutine called by the runner below...
        # Wait until the window is closed.

        # We need a future that stays pending until app exit
        future = loop.create_future()
        app.aboutToQuit.connect(lambda: future.set_result(None))

        await future

if __name__ == "__main__":
    try:
        # Bootstrapping qasync
        # Depending on qasync version, loop.run_until_complete might be needed.
        # Standard pattern:
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)

        # Instantiate window here to ensure it's created within the loop context if needed,
        # though usually Qt widgets can be created before loop start.
        window = MainWindow()
        window.show()

        with loop:
            loop.run_forever()
    except KeyboardInterrupt:
        pass
