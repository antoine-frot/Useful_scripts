#!/usr/bin/python3

import argparse

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Expand the VESTA boundaries from 0 1 to -0.49 1.49.")
    parser.add_argument("input", nargs='+', type=str, help="VESTA input file(s).")
    args=parser.parse_args()

    for input_file in args.input:
        with open(input_file, "r") as f:
            lines = f.readlines()

        with open(input_file, "w") as f:
            iterator = iter(lines)
            for line in iterator:
                if "BOUND" in line:
                    # next is the boundary line
                    f.write(line)
                    next_line = next(iterator, "")
                    next_line = next_line.replace("0", "-0.49").replace("1", "1.49")
                    f.write(next_line)
                    continue
                f.write(line)
