const char *dfb_source(void) { return "controlled"; }
void dfb_sink(const char *value) {}
const char *dfb_source_backup(void) { return "unrelated"; }
void dfb_sink_backup(const char *value) {}

void run(void) {
    dfb_sink(dfb_source());
}
