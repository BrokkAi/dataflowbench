package dfb.joern;

import java.time.Instant;
import java.util.Optional;

/** Prepared source tests for the actual agent traversal. NOT compiled/run in source-only review. */
public final class StartupWitnessAgentTraversalTest {
    private static final Instant BIRTH = Instant.parse("2024-01-01T00:00:00.123Z");

    static final class Fake implements StartupWitnessAgent.Handle {
        final long pid;
        Fake parent;
        Instant born = BIRTH;
        Instant laterBirth;
        int birthReads;
        int parentReads;
        Fake reparentAfterFirst;
        Fake(long pid, Fake parent) { this.pid = pid; this.parent = parent; }
        public long pid() { return pid; }
        public Optional<Instant> birth() {
            birthReads++;
            return Optional.ofNullable(laterBirth != null && birthReads > 1 ? laterBirth : born);
        }
        public Optional<StartupWitnessAgent.Handle> parent() {
            parentReads++;
            return Optional.ofNullable(reparentAfterFirst != null && parentReads > 1 ? reparentAfterFirst : parent);
        }
    }

    static void require(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    static void positiveRootAndSameMillisecondParent() {
        Fake root = new Fake(1, null), parent = new Fake(2, root), child = new Fake(3, parent);
        var chain = StartupWitnessAgent.collectAncestry(child);
        require(chain.termination().equals("root"), "expected root");
        require(chain.nodes().size() == 3 && chain.failureAtDepth() == null, "root shape");
        require(chain.nodes().get(0).pid() == 3L && chain.nodes().get(0).birth().equals(BIRTH) &&
                chain.nodes().get(0).parentPid() == 2L, "node0 same self/directparent sample");
        require(chain.nodes().get(0).parentBirth().equals(chain.nodes().get(1).birth()), "edge birth");
    }

    static void unavailableParentBirth() {
        Fake parent = new Fake(2, null), child = new Fake(3, parent);
        parent.born = null;
        var chain = StartupWitnessAgent.collectAncestry(child);
        require(chain.termination().equals("unavailable"), "must not invent root");
        require(chain.nodes().get(0).parentPid() == 2L && chain.nodes().get(0).parentBirth() == null,
                "retain unknown parent birth");
    }

    static void selfBirthUnavailable() {
        Fake child = new Fake(3, null); child.born = null;
        try { StartupWitnessAgent.collectAncestry(child); throw new AssertionError("accepted missing self"); }
        catch (IllegalStateException expected) { require(expected.getMessage().contains("self birth"), "wrong error"); }
    }

    static void cycle() {
        Fake a = new Fake(1, null), b = new Fake(2, a); a.parent = b;
        var chain = StartupWitnessAgent.collectAncestry(a);
        require(chain.termination().equals("inconsistent"), "cycle must not loop");
        require(chain.nodes().size() <= 2, "cycle not bounded");
    }

    static void selfBirthRace() {
        Fake child = new Fake(3, null); child.laterBirth = BIRTH.plusMillis(1);
        require(StartupWitnessAgent.collectAncestry(child).termination().equals("inconsistent"),
                "self birth mutation accepted");
    }

    static void parentBirthRace() {
        Fake parent = new Fake(2, null), child = new Fake(3, parent);
        parent.laterBirth = BIRTH.plusMillis(1);
        require(StartupWitnessAgent.collectAncestry(child).termination().equals("inconsistent"),
                "parent birth mutation accepted");
    }

    static void parentHandleRace() {
        Fake firstParent = new Fake(2, null), secondParent = new Fake(4, null);
        Fake child = new Fake(3, firstParent); child.reparentAfterFirst = secondParent;
        require(StartupWitnessAgent.collectAncestry(child).termination().equals("inconsistent"),
                "changed direct-parent handle accepted");
    }

    static void impossibleYoungerParent() {
        Fake parent = new Fake(2, null), child = new Fake(3, parent);
        parent.born = BIRTH.plusMillis(1);
        require(StartupWitnessAgent.collectAncestry(child).termination().equals("inconsistent"),
                "younger parent accepted");
    }

    static void finiteBound() {
        Fake head = new Fake(1, null);
        for (int i = 2; i <= 40; i++) head = new Fake(i, head);
        var chain = StartupWitnessAgent.collectAncestry(head);
        require(chain.termination().equals("truncated"), "expected explicit truncation");
        require(chain.nodes().size() == 32 && chain.failureAtDepth() == 31, "32-link bound");
        require(chain.nodes().get(0).pid() == 40L &&
                chain.nodes().get(31).pid() == 9L &&
                chain.nodes().get(31).parentPid() == 8L,
                "terminal parent edge must be exactly32nd link; ancestor7 is outside sample");
    }

    public static void main(String[] args) {
        positiveRootAndSameMillisecondParent(); unavailableParentBirth(); selfBirthUnavailable();
        cycle(); selfBirthRace(); parentBirthRace(); parentHandleRace(); impossibleYoungerParent(); finiteBound();
        System.out.println("9 actual collectAncestry fake-handle tests passed");
    }
}
