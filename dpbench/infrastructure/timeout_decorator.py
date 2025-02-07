####### License: MIT
"""MIT License

Copyright (c) 2015 Aaron Hall

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from __future__ import print_function

import sys
import threading
from time import sleep

try:
    import thread
except ImportError:
    import _thread as thread

try:  # use code that works the same in Python 2 and 3
    range, _print = xrange, print

    def print(*args, **kwargs):
        flush = kwargs.pop("flush", False)
        _print(*args, **kwargs)
        if flush:
            kwargs.get("file", sys.stdout).flush()

except NameError:
    pass


def cdquit(fn_name):
    # print to stderr, unbuffered in Python 2.
    print("{0} took too long".format(fn_name), file=sys.stderr)
    thread.interrupt_main()  # raises KeyboardInterrupt


def exit_after(s):
    """
    use as decorator to exit process if
    function takes longer than s seconds
    """

    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, cdquit, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result

        return inner

    return outer


@exit_after(1)
def a():
    print("a")


@exit_after(2)
def b():
    print("b")
    sleep(1)


@exit_after(3)
def c():
    print("c")
    sleep(2)


@exit_after(4)
def d():
    print("d started")
    for i in range(10):
        sleep(1)
        print(i)


@exit_after(5)
def countdown(n):
    print("countdown started", flush=True)
    for i in range(n, -1, -1):
        print(i, end=", ", flush=True)
        sleep(1)
    print("countdown finished")


def main():
    a()
    b()
    c()
    try:
        d()
    except KeyboardInterrupt as error:
        print("d should not have finished, printing error as expected:")
        print(error)
    countdown(3)
    countdown(10)
    print("This should not print!!!")


if __name__ == "__main__":
    main()
