function dfb_source(): string {
    return "source-one"; // DFB-SOURCE: constant-selector-input
}

function dfb_sink(value: string): void { // DFB-SINK: constant-selector-sink
    console.log(value);
}

function main(): void {
    let value: string;
    switch ("ABC"[2]) {
        case "C":
            value = dfb_source(); // DFB-WITNESS: constant-selector-source-arm
            break;
        case "B":
            value = "safe";
            break;
        default:
            value = "safe";
            break;
    }
    dfb_sink(value);
}

main();
