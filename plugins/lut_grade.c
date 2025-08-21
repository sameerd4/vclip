#include <stdio.h>
#include "plugin.h"

static void run(const char *input, const char *out_dir) {
    printf("[lut_grade] grading %s -> %s\n", input, out_dir);
}

const Plugin lut_grade_plugin = {
    .name = "lut_grade",
    .run = run,
};
