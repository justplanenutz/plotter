#!/bin/bash

# Join arguments with commas to handle as a single CSV string
DATA=$(echo "$@" | tr ' ' ',')

# Use gnuplot with the 'dumb' terminal for ASCII output
# The '-' in 'plot' tells gnuplot to read data from stdin
gnuplot << EOF
    set datafile separator ","
    set terminal dumb
    plot "-" using 0:1 with lines title "Command Line Data"
    $DATA
    e
EOF

