#include <stdio.h>
#include "plugin.h"

static void run(const char *input, const char *out_dir) {
    printf("[encode_export] encoding %s -> %s\n", input, out_dir);
}

const Plugin encode_export_plugin = {
    .name = "encode_export",
    .run = run,
};
