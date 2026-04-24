#!/usr/bin/env python3
import click
import subprocess
import shutil

@click.command()
@click.argument('numbers', nargs=-1, type=float)
def plot_data(numbers):
    """Detects terminal size and plots numbers with custom labels."""
    if not numbers:
        click.echo("Usage: python script.py 10 20 30 40")
        return

    # 1. Determine Terminal Size
    size = shutil.get_terminal_size()
    width = size.columns
    height = max(5, size.lines - 4)  # Leave room for labels/prompt

    # 2. Prepare Data
    data_string = "\n".join(str(n) for n in numbers)

    # 3. Gnuplot Commands
    # 'set xlabel' and 'set ylabel' add the axis descriptions
    gnuplot_commands = [
        f'set terminal dumb size {width} {height}',
        'set ylabel "Mb/s"',
        'set xlabel "Minutes"',
        'plot "-" using 0:1 with lines title "Network Performance"',
        'set grid',
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

