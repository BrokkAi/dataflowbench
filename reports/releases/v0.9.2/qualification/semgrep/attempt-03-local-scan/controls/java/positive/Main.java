import org.yaml.snakeyaml.Yaml;

class Main {
    Object load(String input) {
        Yaml yaml = new Yaml();
        return yaml.load(input);
    }
}
