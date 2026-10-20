struct Holder {
    int value;
};

int dfb_source(void) { // DFB-SOURCE: goto-cleanup-input
    return 1;
}

void dfb_sink(int value) {} // DFB-SINK: goto-cleanup-sink

void run(int failing) {
    struct Holder holder;
    holder.value = dfb_source(); // DFB-WITNESS: goto-cleanup-store
    if (failing) {
        goto cleanup; // DFB-WITNESS: goto-cleanup-transfer
    }
    return;

cleanup:
    dfb_sink(holder.value);
}
