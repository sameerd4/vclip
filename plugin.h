#ifndef PLUGIN_H
#define PLUGIN_H

/**
 * Simple plugin interface for vclip.
 * Each plugin exposes a name and a run function that receives
 * the input video path and an output directory.
 */
typedef struct Plugin {
    const char *name;
    void (*run)(const char *input, const char *out_dir);
} Plugin;

/* Declarations for built-in stub plugins */
extern const Plugin ffmpeg_split_plugin;
extern const Plugin lut_grade_plugin;
extern const Plugin encode_export_plugin;

#endif /* PLUGIN_H */
