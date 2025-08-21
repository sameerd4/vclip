#include <stdio.h>
#include "plugin.h"

static void run(const char *input, const char *out_dir) {
    printf("[ffmpeg_split] processing %s -> %s\n", input, out_dir);
}

const Plugin ffmpeg_split_plugin = {
    .name = "ffmpeg_split",
    .run = run,
};
