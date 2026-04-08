package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"

	"golang.org/x/term"
)

func main() {
	args := os.Args[1:]
	if len(args) == 0 {
		fmt.Println("Usage: go run main.go 10 20 30 40")
		return
	}

	// 1. Determine Terminal Size
	width, height, err := term.GetSize(int(os.Stdin.Fd()))
	if err != nil {
		width, height = 80, 24
	}
	
	plotHeight := height - 5
	if plotHeight < 5 {
		plotHeight = 5
	}

	// 2. Construct Gnuplot Commands
	dataString := strings.Join(args, "\n")
	gnuplotCmds := fmt.Sprintf(`
		set terminal dumb size %d %d
		set ylabel "Mb/s"
		set xlabel "Minutes"
		set grid
		plot "-" using 0:1 with lines title "Network Performance"
		%s
		e
	`, width, plotHeight, dataString)

	// 3. Print Green ANSI Escape Code
	fmt.Print("\033[32m") 

	// 4. Execute Gnuplot
	cmd := exec.Command("gnuplot")
	cmd.Stdin = strings.NewReader(gnuplotCmds)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
	}

	// 5. Reset Terminal Color
	fmt.Print("\033[0m")
}

