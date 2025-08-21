#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "plugin.h"

int main(int argc, char **argv) {
    const char *input = NULL;
    const char *out_dir = NULL;
    const char *pipeline = NULL;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--input") == 0 && i + 1 < argc) {
            input = argv[++i];
        } else if (strcmp(argv[i], "--out-dir") == 0 && i + 1 < argc) {
            out_dir = argv[++i];
        } else if (strcmp(argv[i], "--pipeline") == 0 && i + 1 < argc) {
            pipeline = argv[++i];
        } else {
            fprintf(stderr, "Unknown or incomplete argument: %s\n", argv[i]);
            return 1;
        }
    }

    printf("input: %s\n", input ? input : "(none)");
    printf("out dir: %s\n", out_dir ? out_dir : "(none)");
    printf("pipeline: %s\n", pipeline ? pipeline : "(none)");

    const Plugin *available[] = {
        &ffmpeg_split_plugin,
        &lut_grade_plugin,
        &encode_export_plugin,
        NULL
    };

    if (pipeline) {
        char *copy = malloc(strlen(pipeline) + 1);
        if (!copy) {
            fprintf(stderr, "Out of memory\n");
            return 1;
        }
        strcpy(copy, pipeline);
        char *token = strtok(copy, ",");
        while (token) {
            const Plugin *found = NULL;
            for (int i = 0; available[i]; ++i) {
                if (strcmp(available[i]->name, token) == 0) {
                    found = available[i];
                    break;
                }
            }
            if (found) {
                printf("Loading plugin: %s\n", found->name);
                found->run(input ? input : "", out_dir ? out_dir : "");
            } else {
                printf("Unknown plugin in pipeline: %s\n", token);
            }
            token = strtok(NULL, ",");
        }
        free(copy);
    }

    return 0;
}
