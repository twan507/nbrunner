# app/modules/my_module.py


def say_hello(name="World"):
    """
    Một hàm ví dụ để chào hỏi.
    """
    return f"Hello, {name} from my_module!"


def add_numbers(a, b):
    """
    Một hàm ví dụ để cộng hai số.
    """
    return a + b


def print_current_path():
    """
    In ra đường dẫn hiện tại của script.
    """
    import os

    print(f"Current working directory from my_module: {os.getcwd()}")
