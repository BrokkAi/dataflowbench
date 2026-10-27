import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.constructor.SafeConstructor;

class Main {
    Object load(String input) {
        Yaml yaml = new Yaml(new SafeConstructor(new LoaderOptions()));
        return yaml.load(input);
    }
}
