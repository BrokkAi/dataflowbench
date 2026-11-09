function dfb_source() {
    return "source-one"; // DFB-SOURCE: constant-selector-input
}

function dfb_sink(value) { // DFB-SINK: constant-selector-sink
    console.log(value);
}

function main() {
    let value;
    switch ("ABC"[1]) {
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
