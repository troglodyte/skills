# Symptom → Pattern

Find the row matching what the code is doing, not the pattern you already had in mind. The third column is what the candidate has to beat - often it wins.

| Symptom in the code | Candidate | Direct version to beat |
|---|---|---|
| Branching on a type/mode to pick an algorithm | Strategy | A function taking the algorithm as a parameter |
| Branching on a type/mode to pick *behavior across many methods* | State | A field plus conditionals |
| Constructor with many optional args; telescoping overloads | Builder | Options struct / named or default args |
| Caller must know which concrete class to instantiate | Factory Method | A function that returns the right thing |
| Whole families of related objects must stay consistent | Abstract Factory | Passing the family in as one parameter |
| Third-party interface doesn't match yours | Adapter | A wrapper function |
| Need to add behavior at runtime without touching callers | Decorator | A parameter or flag |
| Callers wading through a complicated subsystem | Facade | A module with a small public surface |
| Tree of things where leaf and container are used alike | Composite | Recursion over a plain nested type |
| State change must notify an unknown, changing set of listeners | Observer | Direct calls, if the set is known and small |
| Request must pass through handlers of unknown length/order | Chain of Responsibility | An ordered list you loop over |
| Operations need to be queued, logged, or undone | Command | A function value |
| Same algorithm skeleton, a couple of steps differ | Template Method | Passing the differing steps in (usually better) |
| Iterating a structure whose internals should stay hidden | Iterator | The language's native iteration protocol |
| Need to snapshot and restore state | Memento | Copying the value |
| Classes coupled to many peers, hard to change one | Mediator | Fewer classes |
| Must add operations across a stable structure often | Visitor | A function that switches on type |
| Truly one instance, needed everywhere | Singleton | Pass it as a parameter (nearly always better) |
| Copying objects without depending on concrete classes | Prototype | A clone/copy method |
| Enormous object count exhausting memory | Flyweight | Measure first - usually not the bottleneck |
| Control access, lazy-load, or intercept calls to an object | Proxy | Doing the work eagerly |

## Resources

- [Refactoring Guru - Design Patterns Catalog](https://refactoring.guru/design-patterns/catalog)
- Its "Relations with Other Patterns" section is the best tiebreaker when two candidates look equally good.
