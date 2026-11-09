function dfb_source() { // DFB-SOURCE: constant-selector-input
    return "source-one";
}

function dfb_sink(value) { // DFB-SINK: constant-selector-sink
    console.log(value);
}

function main() {
    let value;
    switch ("ABC".charAt(2)) {
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
