"""Hash-bound Joern invocation and environment semantics."""
import os

BASE='adapters/joern/swift-normal-v1'

def env_for(rt):
    env=dict(os.environ)
    # Do not accept ambient JVM/Scala injections into a pinned invocation.
    for key in ['JAVA_TOOL_OPTIONS','_JAVA_OPTIONS','JDK_JAVA_OPTIONS','CLASSPATH','JAVA_OPTS','JDK_JAVA_OPTIONS']:
        env.pop(key,None)
    env.update(JAVA_HOME=rt['java_home'],SWIFTASTGEN_BIN=rt['astgen'],JAVA_OPTS='-Xmx512m -XX:ActiveProcessorCount=2',LANG='C',LC_ALL='C')
    return env



def compiler_argv(rt,case,directory):
    return [rt['compiler'],'-module-name','DataFlowBenchTaintSwift','-swift-version','6','-Onone','-sdk',rt['sdk'],'-target','arm64-apple-macosx27.0.0','-module-cache-path',str(directory/'cache'),*[str(directory/'DataFlowBenchTaintSwift'/n) for n in case['fixture_files']],'-typecheck']


def frontend_argv(rt,directory):
    return [rt['frontend'],str(directory/'DataFlowBenchTaintSwift'),'--build-log-path',str(directory/'build.log'),'--output',str(directory/'cpg.bin')]


def query_argv(root,rt,directory):
    return [rt['joern'],'--script',str(root/BASE/'query.sc'),'--param','cpgPath='+str(directory/'cpg.bin'),'--param','configPath='+str(directory/'config.json'),'--param','outputPath='+str(directory/'graph.json')]
