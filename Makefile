CC ?= cc
CFLAGS = -std=c11 -Wall -Wextra -I.
SRCS = src/main.c \
       plugins/ffmpeg_split.c \
       plugins/lut_grade.c \
       plugins/encode_export.c

vclip: $(SRCS) plugin.h
	$(CC) $(CFLAGS) $(SRCS) -o $@

.PHONY: clean
clean:
	rm -f vclip
