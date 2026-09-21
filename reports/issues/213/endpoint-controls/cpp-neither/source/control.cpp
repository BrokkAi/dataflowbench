const char *dfb_source(void) { return "controlled"; }
void dfb_sink(const char *value) {}
const char *dfb_source_backup(void) { return "unrelated"; }
void dfb_sink_backup(const char *value) {}

void run(void) {
    // dfb_sink(dfb_source()) is text, not a resolved call.
    const char *text = "dfb_source dfb_sink";
    const char *(*dfb_source)(void) = dfb_source_backup;
    void (*dfb_sink)(const char *) = dfb_sink_backup;
    dfb_sink(dfb_source());
    dfb_sink_backup(text);
}
