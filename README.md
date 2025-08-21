# vclip

vclip is a simple command-line video processing tool. It parses a pipeline of
processing steps and runs stub plugins demonstrating how a real system might be
structured.

## Building

This project uses a straightforward `Makefile`. Ensure you have a C compiler
installed and run:

```sh
make
```

This produces the `vclip` executable in the project root.

## Usage

```
./vclip --input INPUT_FILE --out-dir OUTPUT_DIR --pipeline ffmpeg_split,lut_grade,encode_export
```

The program prints the parsed arguments and executes each plugin in the order
specified. The current implementations are stubs and simply print the actions
they would perform.
