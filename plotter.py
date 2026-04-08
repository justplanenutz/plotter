#!/usr/bin/env python3
import click
import subprocess
import shutil

@click.command()
@click.argument('numbers', nargs=-1, type=float)
def plot_data(numbers):
    """Detects terminal size and plots numbers to fill the screen."""
    if not numbers:
        click.echo("Usage: python script.py 10 20 30 40")
        return

    # 1. Determine Terminal Size
    # columns (width) and lines (height)
    size = shutil.get_terminal_size()
    width = size.columns
    height = size.lines - 2  # Subtracting 2 to account for the prompt/header

    # 2. Prepare Data
    data_string = "\n".join(str(n) for n in numbers)

    # 3. Gnuplot Commands
    # 'set terminal dumb size' sets the dimensions of the ASCII plot
    gnuplot_commands = [
        f'set terminal dumb size {width} {height}',
        'plot "-" using 0:1 with lines title "Full Screen Data"',
        data_string,
        'e'
    ]

    command_input = "\n".join(gnuplot_commands)

    try:
        subprocess.run(['gnuplot'], input=command_input, text=True, check=True)
    except FileNotFoundError:
        click.echo("Error: Gnuplot not found in PATH.", err=True)

if __name__ == '__main__':
    plot_data()

