# Changelog

This file is the canonical record of user-visible PRIK changes. Add changes to
**Unreleased** as they land, then move them into a versioned section during
release preparation. Versions use [Semantic Versioning](https://semver.org/);
release tags add a leading `v` to the package version.

## Unreleased

- A contract's `__all__` selects declarations by exact spelling, and a
  declaration already projected to no Python namespace keeps that projection.
  Names were compared case-insensitively, so `__all__ = ["Foo"]` published a
  declaration written `foo` although Python names are case-sensitive; and an
  empty export list read as "nothing decided yet", so a default publication
  replaced a decision an earlier stage had taken.

- A procedure-local prototype cannot take a name its module imports. Allocating
  its contract spelling held only the module's declared names, so a module
  importing `first_cb` and declaring `cb` inside `first` wrote a prototype that
  shadowed the import the contract also writes.

- A merged generic keeps specifics that two contributing modules spell alike.
  Specific procedures were looked up by name alone, so a second contributor's
  `to_value` looked like the first and was dropped, losing a signature the
  generic must dispatch over. A specific is now identified by the module
  declaring it, and a contract writing two of them gives each its own Python
  name and names it in the matching `@overload(...)`.

- A `use` that only renames still carries the rest of its module. The parser
  recorded `use m, p => q` exactly as `use m, only : p => q`, so everything
  else `m` publishes was dropped, and the renamed entity was also still
  reachable under its own spelling. A mapping now records whether its statement
  narrowed to an `only` list, which is what separates the two forms.

- A contract's `__all__` decides what it publishes when it is read back. A
  prototype and a generic are written into the body so annotations and dispatch
  resolve, and both read back public by default, so a contract that withheld
  them from `__all__` still had a public export completed for them. Export
  policy now names only the surface the contract states; the declarations stay
  written and reachable for naming and import resolution.

- A prototype is identified by the scope declaring it, and its contract
  spelling is allocated against the names the module already holds. Joining the
  scope to the name produced a spelling that could collide with a real
  declaration -- a module-level `first_cb` beside `first`'s own `cb` -- so the
  two became one prototype and a callback was typed by the other's signature.
  Two scopes whose joined spellings coincided (`a_b` declaring `c`, `a`
  declaring `b_c`) collided the same way. Each now keeps a distinct contract
  name, and a module's own block still publishes the spelling another module
  imports it by.

- A generic assembles the specifics of every accessible interface that
  contributes to it. A module importing `convert` from two modules that each
  declare a generic of that name kept only the first, silently losing the
  other's specific procedures, and importing both without declaring one locally
  dropped the name entirely as an ambiguity. Contributors are now gathered in
  source order through every route, transitively, with one declaration counted
  once; accessibility still applies at each hop, and a generic is still not
  published into a second Python namespace.

- A use-associated name is resolved from every route carrying it, whichever
  way each route entered. A module writing `use a_mod, only : x` beside a plain
  `use c_mod` that also offers `x` reaches two different entities, and the
  named route was examined first and published `a_mod::x` as the canonical
  owner -- which a re-exported module variable then generates native access to
  directly, so the Fortran compiler never diagnoses the ambiguity. Routes that
  name one entity still resolve, and a plain `use` of a module PRIK never read
  carries no assumed name.

- An enum's enumerators are carried by `use` like the constants they are. A
  plain `use` of a module declaring `enumerator :: red = 1` carried nothing for
  `red`, and naming it in an `only` list produced a re-export of unknown kind,
  which the module-variable publication machinery does not attach. Enumerators
  are now read as variables wherever this layer reads a module's declarations,
  including as declaration dependencies when an enumerator's value names an
  imported constant.

- Following a name through an intermediate module applies that module's own
  accessibility. A module importing `x` and declaring `private :: x` no longer
  passes a route to the declaration behind it, and a module reaching two
  different `x` no longer resolves to whichever route was read first. Both
  cases are now reported unresolved, as a direct import of two disagreeing
  routes already was.

- A generated contract publishes a prototype or a generic only where the
  module makes it reachable. A `private` abstract interface and a `private`
  generic were written into `__all__` although the module keeps both to
  itself, and an interface block written inside a contained procedure was
  promoted to a module publication -- so two procedures each declaring
  `abstract interface ... cb` shared one prototype, and the second was given
  the first's signature. Such a block now takes its own scope-qualified
  contract name, stays out of `__all__`, and each procedure's callback is
  typed by the interface its own scope declares.

- Generated Fortran continuation never breaks a line inside a character
  literal. A long call was split at every comma, so an argument such as
  `'alpha, beta'` continued mid-literal and compiled to `alpha,  beta` -- a
  different string, with no diagnostic. Lines now break at the call's own
  arguments, which also keeps a nested call whole.

- A character constant may state its kind before the opening quote, so
  `character(kind=c_char, len=3), parameter :: tagged = c_char_'abc'` is
  published and returned as `abc`. The kind-prefixed spelling was not
  recognized as a literal at all, leaving the parameter with no value and the
  build refusing it as an unsupported module variable. One reader now decides
  what a whole character literal is, so `'a' // 'b'` is recorded as the
  expression it is rather than as a literal.

- A character parser model records its selector through
  `FortranVariable.record_character_selector`, which reads the length, the
  kind, and whether the stored text is a length in one place. A model built by
  hand -- the type-mapping report's rows, a test -- now states the same facts a
  parsed declaration does instead of leaving them to a second reader of the
  joined `kind` text. Semantic conversion reads that recorded selector as the
  authority for a character kind, so a model carrying only the selector is not
  reported as the default character kind.

- Compile-time specialization reaches only the fields that hold declaration
  expressions. Every semantic metadata string was resolved as an expression,
  so a recorded decision spelling a parameter's name -- a pointer's
  `runtime` association in a module that also declares `integer, parameter ::
  runtime` -- was replaced by that parameter's value. Shapes, bounds,
  character lengths, initializers, and default values specialize as before.

- A character declaration's kind is read whole, so
  `character(len=8, kind=max(c_char, 1))` states the kind it writes. The kind
  was found again inside the selector's joined spelling with a pattern that
  stops at the first comma, cutting a kind expression holding a comma of its
  own down to `max(c_char`.

- A Fortran character constant reaches Python holding the characters it
  declares. Fortran doubles a quote to hold one, which Python reads instead as
  two literals written side by side and joins, so
  `character(len=5), parameter :: word = 'don''t'` was published and returned
  as `dont` -- four characters under a declared length of five. Both the
  generated contract and the built extension now state `don't`.

- A generated contract states a character constant's own contents. Respelling
  the Fortran spellings Python writes differently reached inside the literal
  too, so `character(len=6), parameter :: text = ".true."` was published as
  `Final[String[6]] = 'True'` -- a different value, and one contradicting its
  own declared length. A logical or a real written the same way outside quotes
  is respelled as before.

- A raw address contract accepts an extent built from the declaration calls
  PRIK supports, so `Addr(Float64[max(n, m)])` and `Addr(Float64[abs(n)])` are
  no longer refused as unresolved. Deciding that by scanning the extent's text
  counted the call's own name among the values it reads, which no argument
  carries. An extent naming something no argument supplies, a runtime extent,
  and an unsupported call are refused as before.

- TA-Lib's pinned reference harness now preserves binary64 array inputs across
  its preliminary JSON self-checks, preventing architecture-dependent BETA
  mismatches without weakening the 322-indicator PRIK comparison.

- A module variable's canonical wrapper plan is now owned by its declaring
  native module and name. Adding, removing, or renaming Python facades changes
  only namespace publications, so support-operation and holder identities no
  longer move between facades.

- Generated Fortran contracts distinguish a module's dependencies from its
  Python publications without changing Fortran accessibility. An implicitly
  public imported name used by that module's own declarations remains
  semantically reachable through the module and available to express the
  contract, but reaches Python there only when named in a `public` statement.

- Fortran use-association accessibility now honors `public` and `private`
  statements that name an imported module, including entities reached through
  multiple routes. Plain `use` discovery also carries named generic and
  abstract interfaces through the semantic accessibility graph.

- A contract may publish a module variable only through a facade, leaving the
  namespace declaring it out of Python entirely. Owning the one native variable
  plan used to put that namespace there anyway, so a package hiding its
  declaring module exposed it regardless.

- A published Fortran `parameter` is documented as what it is. Each namespace
  receives the declared value as an ordinary Python attribute: assignment is
  not refused, rebinding one name leaves the Fortran parameter unchanged, and
  it does not rebind any other namespace publishing the same parameter. The
  reference previously called this a read-only constant.

- A module publishing a re-exported name links again when that alias is the only
  thing it needs a bundled helper for. Binding an alias calls one, but a module
  with no arguments, results, module variables or derived-type fields was
  treated as needing none, so the generated extension referenced
  `prik_bind_namespace_alias` without carrying it and failed to import.

- A module-variable re-export now publishes another live route to the declaring
  variable instead of being omitted or rejected. Every namespace reuses one
  completed variable plan and its native accessors, so scalar assignment, array
  mutation, allocation, pointer association, derived state, and read-only
  parameters retain one native identity. Generic interfaces remain publishable
  only by their declaring namespace.

- A wrapper's Python names are decided once, by post-IR export policy, and
  every stage that writes a name reads that decision. The `.pyi` printer
  allocated its own instead, so a build and the contract describing it could
  disagree: a C function named for a Python keyword built as `lambda_` while
  its contract said `def lambda(`, which is not Python at all. Worse, the two
  allocators walked declarations in different orders -- policy takes classes,
  functions, overloads, then variables, the printer took variables before
  functions -- so a module variable and a procedure whose names both normalize
  to `lambda_` were settled one way by the build and the other way by the
  contract. The contract then held the right set of names attached to the wrong
  declarations. A contract now names exactly what the build beside it
  publishes, derived types included, and records the source spelling with
  `@bind` wherever the two differ.

- A wrapped type is spelled like the Python class it becomes. Fortran writes
  one declaration under many spellings, so PRIK picks one, and picking
  `point_t` for something used as `Point_T(...)` read as a function. A derived
  type now publishes with each underscore-separated word capitalized --
  `type :: point_t` reaches Python as `Point_T` -- while every other Fortran
  declaration stays lowercased. Renaming one in the contract still works, so
  this is a default rather than a constraint. This changes the published class
  names of existing Fortran wrappers.

- A C declaration keeps the case it is written in. Folding it is a Fortran rule,
  correct there because Fortran writes one declaration many ways and none of
  the spellings is its own. C names each declaration exactly, so folding both
  lost that name -- `BarBaz` reached Python as `barbaz` -- and invented
  collisions the source does not have: `Foo` and `foo` are two functions, and
  they arrived as `foo` and `foo_2` with nothing to say which was which. This
  changes the published names of existing C wrappers. Folded import lookup now
  succeeds only when it identifies one declaration, rather than selecting an
  ambiguous spelling by insertion order.

- The contract a source build writes beside its artifacts states published
  Python names. It stated raw source spellings, so a Fortran build wrote
  `def SCALE_VALUE(` next to a module exposing `scale_value`.

- A re-exported declaration is owned by the contract declaring it, whichever
  order an entry contract imports from. The namespace encountered first owned
  it, so a facade listed before the module it reads from took ownership of a
  procedure it only republishes.

- A wildcard import reads the surface its dependency publishes, where it used to
  take every name that dependency held. A withheld name stays reachable by
  asking for it, which a contract needing it to express a declaration -- or
  meaning to publish it itself -- still does.

- A contract's `__all__` names its sub-namespaces as well, so leaving one off
  keeps the package from exposing it. A generated entry contract states the
  modules it imports for that reason, and a contract stating no list still
  publishes everything it reaches.

- A contract states everything it publishes in a closing `__all__`. An import
  cannot say whether a name is needed to express a declaration or meant to be
  published, because a rename reads the same either way, so the list settles it.
  PRIK writes what the source publishes -- the module's own public declarations,
  explicitly public imports, and implicitly accessible imports that are not
  declaration dependencies -- and the list is there to be edited: remove a name
  to stop publishing it, add an imported one to publish it, or remove the list
  to publish everything the contract reaches. Reading C
  source states the same thing through `--export-symbols` /
  `build_c_extension(export_symbols=...)`, which selects the source-side public
  surface and writes the corresponding Python names into the generated
  contract's `__all__`.

- A re-exported procedure binds the callable its declaring module exported
  rather than being wrapped again, so a contract build gives the same object a
  source build does, under a renamed re-export as well.

- A published name is followed to the module declaring it, however many
  modules published it along the way. Reading only the module a `use` names
  left a name published twice over looking like nothing at all, and the
  re-export was dropped.

- A generated contract states a re-export by aliasing the name to itself, the
  way a stub marks anything it publishes, so an import written to express a
  declaration is no longer republished. Source and contract builds agree on
  what a module exports; a package entry contract still selects its surface by
  importing, which is what such a contract is for.

- A generic declared inside a procedure is no longer read as one of its
  module's own, and an import binds the name a collision made its declaring
  contract use rather than one derived from the source spelling.

- Publishing an imported name re-exports it at runtime only where the name is
  one Python object to bind. A module publishing an imported callback prototype
  states where a signature comes from, and a signature is not an object, so
  binding one reached for an attribute of a module that exports nothing and the
  build failed outright. Each re-export now records what it publishes, and only
  a procedure or a derived type becomes a runtime alias; every other kind keeps
  to the semantic and contract-import paths that already carry it.

- A re-export binds the Python name its declaring module actually published
  rather than the Fortran spelling it was written with, so publishing an entity
  spelled in capitals no longer looks up an attribute that does not exist.

- A plain `use` now re-exports the accessible names it carries unless a name is
  only a dependency of the importing module's declarations. An explicit
  `public` statement still publishes that dependency; an origin that two used
  modules could supply stays unresolved rather than guessed.

- A generic interface built from several blocks merges within the scope
  declaring it. Two procedures of one module may each declare an interface of
  the same name, and merging them on the module they share let one procedure's
  specifics answer the other's calls.

- A generated contract writes an overload's target and a prototype import the
  way the contract declaring them spells each one. The overload named a source
  spelling that matched no declaration it holds, and a prototype's spelling was
  kept for every module using that name rather than the one declaring it.

- A contract can now rename what it declares. `SourceName` states the native
  entity a variable or constant reaches, the way `bind` already did for a
  callable, instead of replacing the name the declaration states -- editing a
  contract to give an entity a Python name exported the source spelling and
  dropped the edit. A source name inside `Final[...]` reaches its declaration
  as well, where it was previously ignored. A generated contract is affected
  too: a Fortran entity Python cannot spell, such as one named `lambda`, is
  declared as `lambda_` and now stays reachable under that name.

- A class can state the native type it reaches through `bind`, so a derived
  type can be exported under a different Python name. An imported class
  reference resolves through the name its declaring contract states, and a
  renamed class keeps its `bind` when the contract is regenerated.

- A generated Fortran contract no longer records a source spelling that differs
  from its Python name only by case. Fortran names entities without regard to
  case, so a capitalized `IK` written as `ik` renames nothing and the generated
  Fortran reaches it either way; every such declaration nevertheless carried a
  `SourceName` or `@bind` stating the capitals back. A name Python cannot hold
  as written -- a keyword, an illegal character, one a collision moved aside --
  is a real rename and still keeps its original, as does every name from a
  source language that is case-sensitive.

- A generated contract now imports each name under the spelling the contract
  that defines it uses. A source-derived contract declares a Fortran entity
  under a Python name, so one spelled in capitals is declared lower case, while
  the import kept asking for the source spelling and named nothing the
  dependency defines -- loading the package back failed on it. A prototype is
  unchanged: it keeps its declared spelling wherever it is written, so an import
  binding one keeps it too.

- An overload declaration whose specific projects an output argument into its
  result is now accepted. The check compared the declared result against the
  projected one including the write-through the native argument passing states,
  and a native scalar descriptor result including the descriptor topology that
  only a `native_call` result wrapper can name -- neither of which a declared
  result type spells. A generated contract carrying such a generic, for example
  one over `intent(out)` allocatable arguments, was rejected on read-back by the
  same tool that wrote it.

- A contract generated from a source whose abstract interface types a dummy
  through a kind of its own now resolves that kind. An interface body's
  variables reached no target probe, so a kind named only there -- through a
  `use` written inside the body -- had no storage fact and `generate --pyi`
  failed on a declaration the wrapper build accepted.

- A derived type building one generic binding from several `generic ::`
  statements now collects every specific into that binding. Each statement was
  recorded as its own binding of the same name, so only the first reached
  dispatch and calling the generic with the argument types of any later
  statement raised `no matching overload`.

- A scope naming the same module in several `use` statements now keeps every
  import. Each statement was replacing the previous one, so only the last
  survived; a module splitting a long import list across lines silently lost
  the names the earlier lines carried, and any kind parameter among them stopped
  resolving.

- A procedure whose outputs have no completed ordering is now reported as an
  unsupported wrapper policy instead of raising a comparison error.

- Generated Fortran module leaves now import sibling contracts relatively, so
  building a leaf directly loads the contracts its declarations depend on.
  A native derived type exported through several modules shares one set of
  generated support procedures.

- A module that names an imported procedure in a `public` statement now
  publishes it, so a facade module reaches Python instead of disappearing. The
  declaration is not repeated: the published name binds to the one wrapper its
  declaring module exposes, so `facade.proc is home.proc`, and the contract
  keeps spelling the re-export as the import it already was. A name public only
  because the module default is public states no such intent and is unchanged.

- A generic interface that repeats a `use`-associated name now extends that
  generic instead of replacing it, so the importing module dispatches to the
  specifics it inherited as well as its own. Accumulation stays one-directional,
  as Fortran requires: the declaring module does not gain what a later module
  adds. An inherited specific is reachable only through the generic, because the
  import never bound its own name.

- A generic interface may now be declared across several blocks in one scope,
  which Fortran allows and real sources use to add specifics under
  preprocessor guards. The blocks become one generic carrying every entry in
  declaration order, instead of being rejected as a duplicate declaration.

- A callback interface reached through renaming re-exports now records the name
  its declaring module gives it. The reference followed the module back to the
  declaration but kept an alias from partway along the chain, so it named a
  symbol that module does not define.

- The semantic IR now carries a strided axis as `::`, the spelling a contract
  uses, instead of a longer internal token. `prik semantics` output changes
  accordingly; contracts, docstrings and generated sources are unaffected
  because they already printed the contract spelling.

- Removed the `Strided` contract name and the dimension step that carried it.
  `T[::]` already spells a strided axis and `T[:]` a contiguous one, so the
  longer `T[::Strided]` and `T[0:n:Strided]` forms are gone rather than kept as
  a second way to write the same contract. A value in a dimension's step
  position is now rejected with a message naming the spelling to use.

- A callback interface's result now keeps the declaring module's type identity,
  matching its dummies. An imported function interface returning a type its own
  module declares previously attributed that type to the consuming module and
  failed to build, both from Fortran source and from a generated contract.

- A renamed callback import keeps the declared interface name beside the local
  one, so a contract imports `OBJ as LOCAL_OBJ` rather than a name the declaring
  module never defines. A reference that differs from the declaration only in
  case is now spelled canonically instead of binding a second name.

- Following a re-exported callback interface respects Fortran accessibility. A
  module that imports an interface privately no longer exposes it to a later
  `use`, and the rule applies at every hop of a chain.

- An abstract interface imported from another module now converts in the scope
  of the module that declares it. A derived type the interface names belongs to
  that module, so wrapping a consumer that imports only the interface — and not
  the types it mentions — no longer fails against a type identity attributed to
  the consuming module.

- Callback interface resolution now covers a `use` inside a single procedure, a
  standalone procedure's own imports, and an interface re-exported through any
  number of modules. File, project, and `generate --pyi` conversion share one
  resolver rather than each carrying its own lookup, and a contract that
  re-exports a prototype resolves back to the module that declares it.

- A contract now imports a prototype it references but never declares, so an
  interface named by a procedure-local `use` is bound in the generated `.pyi`
  instead of appearing as a free name.

- Callback docstrings now state each array argument's rank and extents. Every
  generated docstring and diagnostic spells a runtime extent with the shorthand
  a contract uses (`Float64[::]`) rather than the explicit step the IR stores
  (`Float64[::Strided]`); the two are the same contract, while `Float64[:]`
  remains the distinct contiguous one.

- A primitive scalar callback dummy the callee may write now reaches Python as
  rank-zero storage (`Out(Float64[()])`) instead of an independent value, so
  the value the callback computes reaches the native caller. This covers
  `intent(out)` and `intent(inout)`, and also a dummy with no declared
  `intent`, which Fortran permits the callee to modify — that case keeps its
  missing direction in the contract as a bare `Float64[()]` rather than gaining
  a synthesized one. `--assume-intent-in-scalars` elects the input-only default
  for it instead. Python has no writable scalar, so the previous `Out(Addr(T))` spelling
  silently discarded the write; it is now a policy error naming the replacement.
  A prototype still mirrors the native argument list — edit it with
  `@native_call` to project an output into the callable's return value instead.

- Generated docstrings now state a callback's exact callable signature —
  arity, per-argument direction and element type, how an output is delivered,
  and the lifetime and fatal-error rules — taken from the same completed
  prototype the trampoline is generated from.

- Assumed-shape array arguments are now supported inside a callback prototype.
  A `procedure(iface)` dummy whose interface declares `values(:)` lowers to an
  assumed-shape bridge dummy and a contiguous call-local copy measured from it,
  instead of emitting an invalid array declaration. Array callback *results*
  still require an exact shape and now report that directly.

- A dummy procedure's interface name keeps the spelling it was declared with.
  Generated `.pyi` contracts previously annotated `procedure(OBJ)` as `obj`
  while importing `OBJ`, so PRIK could not rebuild from the contract it had
  just written.

- `prik generate --pyi` now resolves an abstract interface imported from
  another supplied source file, matching multi-file wrapper builds.

- A `procedure(iface)` dummy whose interface no supplied source declares now
  reports the interface by name and asks for the module that declares it,
  instead of failing against an opaque placeholder type. Contract extraction
  spells that interface name so the generated `.pyi` stays consistent with the
  import it already emits.

## 0.5.0 — 2026-09-13

- Added CMake integration through the packaged `UsePRIK.cmake` helper and a
  `prik generate --cmake` standalone-project mode. CMake generates PRIK wrapper
  sources as build outputs and owns native compilation, linking, external
  targets, and incremental rebuilds while preserving per-source flags,
  compiler-required ABI options, preprocessing dependencies, and linker
  language from PRIK's completed build plan.

- CMake contract modules now distinguish semantic `NATIVE_LANGUAGE` from the
  final `LINKER_LANGUAGE`, keep native compilation flags target-local, and
  report a clear error when CMake's C language is not enabled.

- CMake dependency targets now propagate their native compile usage
  requirements, and standalone `--cmake --lto` initializes IPO for native and
  generated targets.

- CMake configuration no longer runs PRIK's semantic pipeline. It asks for a
  structural plan -- deterministic generated filenames, the link driver, and
  compiler-profile ABI flags -- and the full pipeline then runs once at build
  time. Configuring a 300-procedure module's plan drops from about 2.5s to
  0.4s, and the structural query no longer grows with source size.

- Generated CMake targets have a fixed source list. The optional collision
  adapter and Fortran bridge units are always written, holding a
  symbol-free placeholder when unused, so a semantic edit changes file
  contents instead of the build graph and never forces a CMake reconfigure.
  Transitive semantic inputs now reach CMake through a generated dependency
  file, which raises the CMake floor for the packaged helper to 3.21.

- `prik generate --cmake` keeps each native link input in its own CMake
  category: prebuilt objects, archives, and shared libraries stay filesystem
  paths in `LINK_LIBRARIES` instead of becoming ambiguous relative tokens,
  while library names and linker arguments keep their meaning and order.

- CMake native object targets receive `LINK_LIBRARIES` with the caller's link
  syntax unchanged, so `debug`/`optimized` keywords and generator-expression
  entries keep selecting usage requirements per configuration instead of being
  flattened or dropped.

- CMake mode rejects a `.C` source suffix, which CMake compiles as C++ while
  PRIK plans the source as C, and reports a clear error when a module
  contributes native Fortran sources without CMake's Fortran language enabled.

- `prik_add_module()` accepts `LIBRARY_DIRS`, mapping it to
  `target_link_directories()` and the extension's `BUILD_RPATH`.
  `generate --cmake` translates `--native-library-dir` into `LIBRARY_DIRS`, so
  a shared native library outside the system search path is found both at link
  time and on import without `LD_LIBRARY_PATH`.

- `prik-build.json` schema 5 records generated/native compilation-unit ABI
  flags and explicit native linker-language requirements.

- PRIK's CMake modules are packaged inside the `prik` distribution and
  discovered automatically. scikit-build-core builds pick the directory up
  through a `cmake.module` entry point, so `include(UsePRIK)` needs no lookup,
  and a packaged `PRIKConfig.cmake` makes `find_package(PRIK CONFIG REQUIRED)`
  load the same helper. `prik cmake-dir` prints the packaged module directory
  and `prik install-dir` the prefix PRIK's data files are installed under, for
  `-DPRIK_DIR=` and `-DCMAKE_PREFIX_PATH=`. `cmake_module_dir()` and the
  `share/prik/cmake` installation are unchanged.

- The Ubuntu and macOS unit-test jobs now fail when CMake is missing instead of
  letting the CMake integration tests deselect themselves, and report a missing
  Ninja as a warning because those tests then use the Makefile generator.

- Added the runnable `examples/cmake/` project, which builds one Fortran module
  through every CMake discovery route -- scikit-build-core's entry points,
  `CMAKE_MODULE_PATH`, `PRIK_DIR`, and an installation prefix -- with a script
  that runs each route and calls the built extension.

- PRIK also publishes scikit-build-core's `cmake.root` entry point, which sets
  `PRIK_ROOT`, so a project listing PRIK and `scikit-build-core>=0.11` in
  `[build-system] requires` resolves
  `find_package(PRIK CONFIG REQUIRED)` with no `PRIK_DIR`, `CMAKE_PREFIX_PATH`,
  or `CMAKE_MODULE_PATH`. `include(UsePRIK)` keeps working through the existing
  `cmake.module` entry point.

- A configure-time structural query that fails because PRIK or one of its
  dependencies cannot be imported now names the selected `Python_EXECUTABLE`
  and how to check it, while keeping the underlying error. Other generation
  failures are reported unchanged.

- Added `prik doctor cmake`, which reports the imported package, the
  distribution metadata answering for it, `cmake-dir`, `install-dir`, both
  CMake entry points, and any duplicate installation or `PYTHONPATH` entry that
  could answer instead.

- Array handles support allocatable and pointer arguments, results, module
  variables, derived fields, optional arguments, and matching ordinary-array
  parameters. Numeric and character arrays accept supported forward and
  reversed Fortran sections without copying.

- Character array handles support caller-created and returned storage.
  Deferred-length allocation and resizing use `element_length=...`.

- Wider Fortran logical arrays use the matching-width NumPy integer dtype;
  `logical(c_bool)` arrays use `numpy.bool_`. Handle storage also supports
  `longdouble`, `clongdouble`, and `uintp` where the target exposes them.

- Improved generated-wrapper build time and contiguous-array call overhead.

- **Breaking (native ABI):** native array handles use
  `prik.native_array_backend.v2`. Rebuild extensions that exchange handles.

## 0.4.3 — 2026-08-31

- Republishes 0.4.2. That tag carried the previous package version, so the
  built distribution was rejected as an existing release and never reached
  PyPI. The contents are unchanged.

## 0.4.2 — 2026-08-31

- The `jupyter` extra now accepts IPython 7.0 and newer instead of requiring
  8.0. The cell magics use only long-stable IPython APIs, and the higher floor
  made `pip install prik[jupyter]` upgrade the IPython that hosted notebook
  environments ship, which forced a runtime restart for no benefit. The `qa`
  extra installs `prik[jupyter]` rather than repeating that requirement, so
  the supported IPython range is stated once.

- Added a runnable `examples/notebooks/quickstart.ipynb` and its guided
  tutorial, covering a Fortran cell, a C cell, and reshaping the generated API
  by editing its semantic contract in the same session. The home page, Getting
  Started, the tutorial, and the README offer it as a Colab run or a direct
  download, so the documented workflow can be tried before installing anything.

- Generated contracts now represent a one-level primitive C pointer as
  runtime-rank `T[...]` NumPy storage instead of choosing a scalar temporary.
  It accepts ranks 0 through 15 with any strides, so a Fortran-ordered array
  or a strided slice reaches the native call unchanged, and it can be narrowed
  to contiguous, rank-zero, fixed-rank, or scalar-address storage in an edited
  contract. `Arg(i).size` supplies the total element count to a native
  parameter, alongside the existing `Arg(i).shape[d]` and `Arg(i).strides[d]`
  layout projections; an axis projection against storage that has no such axis
  now raises `TypeError` instead of reading past the actual's shape.

- Getting Started now offers complete Fortran and C paths for toolchain
  verification, building the same first function, and the edit-review-build-test
  loop. Fortran modules now begin in their task-focused User Guide page instead
  of a separate mandatory beginner step.

- Added a dedicated C section to the User Guide for scalar functions, pointer
  contracts, arrays and strings, outputs and errors, and native symbols and
  dependencies. The C Support page now serves as a concise capability and
  boundary map with the same wrapper-area, boundary, and source-entry structure
  as Fortran Support. User Guide navigation presents separate Fortran and C
  paths followed by their shared build workflows.

- An array argument now requires the NumPy storage of the C element type its
  source declares, rather than the canonical storage of the same width. A
  target's `int64_t` may be `long` or `long long`, and NumPy independently
  gives `NPY_INT64` to whichever of the two is 64 bits, so those two choices
  could disagree: a `long long *` buffer asked for `numpy.longlong` on one
  target and `numpy.int64` on another. One C source now keeps one accepted
  dtype everywhere.

- A scalar argument whose native parameter is a 64-bit C integer now accepts
  either NumPy spelling of that width and converts it, so `np.int64` and
  `np.longlong` are both valid for a `long long` or `long` parameter whichever
  one the target calls `int64_t`. Array arguments are unchanged: an element
  buffer cannot be converted, so it still requires the exact native dtype.

- A cell magic that reads a dash-prefixed flag value as another option now
  names the equals form and, for the flag groups, the quoted-group form.

- Added optional `%%fortran`, `%%c`, and `%%pyi` IPython/Jupyter cell magics.
  Native-source cells compile directly or, with `--pyi`, persist their exact
  source and insert editable per-module or direct-declaration contract cells.
  Executing the generated `%%pyi` cell recovers the source language from its
  digest, builds against that cached source, and publishes declared Fortran
  modules or standalone declarations directly in the notebook namespace.
  Exact cells reuse a persistent SHA-256 build cache unless `--force` is
  selected, and PRIK does not expose an internal package entry. Wrapped
  functions follow the published notebook path (`maths.square` or standalone
  `square`) instead of exposing the private cache extension name; ordinary
  file builds retain their user-selected package root, such as
  `geometry.maths.square`. Existing notebook build artifacts are rebuilt once
  so cached extensions cannot retain the old private function identity.
  Multi-module `--pyi` cells are presented sequentially in terminal IPython,
  whose next-input prompt can hold only one editable contract, while Jupyter
  frontends continue to receive every generated module cell immediately. All
  cells in one generated contract bundle retain the source cell's effective
  compiler and build flags; changing that configuration requires regenerating
  the bundle and is rejected before compiler execution. Independently authored
  `%%pyi` cells can instead name one or more existing implementation files with
  `--native-fortran-sources` or `--native-c-sources`; each cell builds and
  publishes only its own contract module, and native file-content changes
  invalidate its persistent cache.

- A one-character `@native_call` literal is now buildable: `String[1]("N")`
  declares the character a native parameter receives instead of leaving it a
  visible Python argument. It crosses the boundary as an interoperable `char`,
  so the same completed decision reaches a bridged Fortran `character(len=1)`
  dummy and a direct `bind(C)` entrypoint. Policy completion requires exactly
  one byte-representable character; invalid values and longer fixed-length
  literals are rejected before planning.

- A `@native_call` computed projection can now state the integer type it is
  materialized as: `Int32(Arg(0).shape[0])` beside the existing `Int32(1)`
  literal form. Shape, stride and length producers previously always crossed
  the boundary as `SizeT`, which is the right identity for a C `size_t`
  parameter but not for a default Fortran `INTEGER`, so those parameters had to
  stay visible in the Python signature. Fixed-width signed and unsigned integer
  contract types and `SizeT` are accepted; unresolved `Int` and `UInt` are
  rejected before planning. The explicit conversion is not range-checked.

- Renamed the exact C scalar mechanism from "cast" to "identity" throughout the
  semantic IR and policy, matching the documented `Exact C Scalar Identities`
  vocabulary and freeing "cast" for the conversion above. The public contract
  helpers (`CInt`, `CLongLong`, and the rest) are unchanged. The semantic-IR
  JSON record emitted by `prik semantics --json` renames its `native_cast`
  projection key to `native_c_identity` and gains a `value_cast` key.

- Added a Pythonic BLAS tutorial and runnable example that reshape `DDOT`,
  `DNRM2`, `DGEMV` and `DGEMM` into `dot`, `norm`, `matvec` and `matmul`, plus
  `DenseMatrix`. An edited `.pyi` contract owns the exact native mapping,
  extents, leading dimensions, transposition modes, array validation, fixed
  numeric values and result allocation. Matrix operations consume
  Fortran-contiguous storage directly, while `DenseMatrix` converts its matrix
  once at construction. The example reuses the existing Reference BLAS sources
  in a four-file contract, Python API, build and test workflow. The `.pyi`
  reference now states the native identity of shape and stride projections and
  the declared-character-literal form.

- Reduced clean-build time for large projects under optimizing compiler flags.
  Generated bindings now bind each ordinary array argument through one shared
  `prik_bind_array` helper instead of emitting the whole validate, extract, and
  native-handle sequence at every array argument of every wrapper. A wrapper
  carries one call and a small table of required extents in place of the
  sequence, so the compiler optimizes the binding logic once rather than once
  per argument per wrapper. Building the 155-source reference BLAS with
  `-O3 -march=native` emits about a third less binding code and compiles it
  about 1.4x faster.

- A binding is always one generated C file. Large procedure-only projects were
  previously split across `<module>_wrapper_001.c` and siblings so those units
  could compile concurrently; every project now generates only
  `<module>_wrapper.c`. Splitting raised total compiler work — each unit
  re-parsed `Python.h` and the NumPy headers — and paid off only where cores
  were idle, which a project's own sources rarely leave. Removing it lowers
  total build work and leaves one file to read when inspecting generated
  output.

## 0.4.1 — 2026-08-27

- Fixed README links and the logo for PyPI rendering. Documentation links now
  open the published website, maintained-library links open their complete
  website guides, and repository files use absolute GitHub URLs.

## 0.4.0 — 2026-08-26

- Reorganized the Reference overview by task and linked every published user
  reference, including the editable `.pyi` format and generated build files.
  The Reference sidebar now follows the same grouped
  structure, with `.pyi` Format followed by the clearly named Editing Contracts
  guide, and the build-file reference clearly distinguishes source and
  semantic-contract generation while showing the structures of both the
  replay manifest and Makefile. The user Reference now presents `.pyi` Format
  as a top-down guide to the distinct Fortran package and C single-file
  layouts, namespace exports, declarations, C- and Fortran-specific forms,
  decorators, native-call entries, types, storage, and metadata, while leaving
  the internal Semantic IR model to the developer Semantics Stage guide.

- Added C-focused FAQ answers for first builds, pointer contracts, supported
  arrays and strings, a runnable existing-library or large-header workflow with
  task-specific follow-up links, and fail-closed unsupported APIs.

- Linked the Language Support overview directly to an expanded **At A Glance**
  comparison, separated the detailed Fortran, C, and shared sections, gave each
  supported and unsupported C capability family its own evidence row, removed
  the ambiguous implementation-route column and empty planned-work placeholder,
  replaced vague lane terminology with explicit C wrapper wording, and made
  Fortran Support a complete guide-linked wrapper overview while retaining its
  concise source-format and public-entrypoint reference. The duplicated
  monolithic Fortran Wrapper Reference and the three redundant generated
  Fortran API pages were removed; their unique public rules now live in
  Fortran Support, the topic-specific User Guide, and `.pyi` Format. The README
  and website homepage now describe C as a focused wrapper subset and name its
  currently supported primitive, one-level-pointer, NumPy-array, and string
  surface without changing PRIK's Fortran-and-C positioning.

- Grouped the maintained library projects under `examples/fortran/` and
  `examples/c/`, with the same Fortran and C grouping in the published example
  navigation. Commands, CI jobs, source-linked documentation, and package
  imports now use the language-specific paths. General documentation names
  both direct-C projects, while the homepage defers their technical details to
  the example guides. The gallery summarizes the hosted compiler and
  architecture matrix, and every project guide records its own tested
  platforms.

- Added a maintained TA-Lib v0.7.1 example with a checked-in semantic contract
  for all 322 double and float-input indicators plus initialization and
  shutdown. Its reviewed inventory accounts for all 522 public functions, its
  edited contract projects TA-Lib's output range metadata, and its
  fail-closed differential harness sends the same request through a direct
  native reference and the PRIK wrapper for every numerical entrypoint. The
  guide explains the common indicator signature, semantic `.pyi` mapping, and
  provenance and limits of those live reference results. Maintained-example
  pages now distinguish the five Fortran source examples from libm and TA-Lib,
  whose wrappers consume public C declarations and link compiled libraries.

- Multi-source Fortran builds compile in dependency order instead of the order
  you listed. PRIK records which parsed file provides each module and
  submodule, resolves the `use` dependencies between them, and groups the
  objects into batches that only depend on earlier batches, so naming a
  consumer before its provider no longer fails the build. Batches within a
  level can compile concurrently; `--jobs N` bounds that. When a compiled
  source was never parsed — an extra `--native-fortran-sources` file, for
  example — or the dependencies cannot be ordered, the build falls back to the
  order you supplied. Discovering sources you did not name, prebuilt module
  search paths, and external libraries remains the caller's responsibility.
  The reference and feature matrix previously described this as unsupported.

- Every Python fence in `docs/` is now checked, not only those on the README,
  Getting Started, and User Guide pages. Each is parsed, and one importing from
  `prik.contracts` is loaded as a semantic `.pyi` contract, so a reference-page
  snippet can no longer drift into a contract that does not load. Two markers
  support this: `prik-doc-test-output` now also tells the audit that a fence
  holds captured output rather than source, and the new
  `prik-doc-contract: invalid` marks a negative example and asserts that
  loading it fails. `docs/developer/workflows/documentation.md` documents the
  marker set. A function selected by `prik-doc-source` is checked together
  with its decorators, so semantic-call mappings cannot drift outside the
  verified excerpt.

- The copied LAPACK example now mirrors Reference LAPACK's default source
  selection: XBLAS-only routines are excluded, the two required `INSTALL/`
  workspace helpers are bundled, and a failed native build now stops without a
  secondary missing-source diagnostic. This makes the maintained 127-routine
  example build consistently on Linux and both hosted macOS architectures.

### Changed

- Removed the redundant user recipe section and the unpublished deferred C
  parser page. Their maintained workflows and evidence now point directly to
  Getting Started, the User Guide, Language Support, and the active API, CLI,
  parser, and preprocessing references.

- Semantic class contracts now use class-level `@native_abi("c")` for Fortran
  `bind(C)` derived types as well as callable entrypoints. The redundant
  `@native_type` decorator has been removed, and the behavior-neutral Fortran
  `sequence` attribute is no longer serialized into semantic `.pyi` or carried
  into wrapper planning. Native teardown operations use one language-neutral
  `@destroy` declaration per operation and remain lifecycle metadata rather
  than public Python methods. The generated class reference also clarifies
  constructor replacement, complete method overload sets, object destruction,
  and when native resource ownership needs custom teardown.

- Fortran feature tests now keep permanent native inputs, reviewed generated
  contracts, edited contracts, and routing cases in one consistent fixture
  layout. The exhaustive primitive-array evidence now belongs to the arrays
  feature, and the documented array journey is checked through both source and
  generated-`.pyi` builds.

- Report commands now share one output rule: **`--json` selects the format and
  `--out` selects the destination, and neither changes the other.** Without
  `--json` every report command prints a human-readable report; with `--json`
  it emits the complete record. `--out PATH` writes whichever format was
  selected, and bare `--out` writes one file beside each input source, using
  `.json` for the record and `.txt` for the report.

  This changes three commands:

  - `parse --out PATH` previously wrote JSON regardless of `--json`; it now
    writes the human-readable report unless `--json` is given. Use
    `parse --json --out PATH` to keep the previous output.
  - `semantics` gains `--json` and `--print-limit`, and now prints a
    human-readable summary by default instead of the complete JSON record. Use
    `semantics --json` to keep the previous standard-output behavior. The
    summary reports each module's functions with their semantic signatures and
    every argument's semantic dtype, rank, ownership, and mutability.
  - `probe` replaces `--format {json,markdown}` with `--json`. The Markdown
    mapping table is now the default standard-output rendering, and the
    Markdown output itself is unchanged.

- `probe` now selects its report from `--expr` rather than from the output
  format. Without `--expr` it measures the standard datatype mapping table, so
  the bare command reports that table instead of an empty measurement; with
  `--expr` it measures the named expressions, which now render in both formats.
  The JSON mapping report adds the structured `target_fact` measurement,
  `recipe`, and `source_text` alongside the displayed text. The mapping report
  now rejects `-I`, `-D`, `-U`, and `--std` instead of accepting options its
  fixed inventory cannot use.

- `prik.pipeline.type_mapping_report` now exposes `c_type_mapping_report()` and
  `fortran_type_mapping_report()` returning measured records, plus
  `type_mapping_markdown()` and `expression_probe_markdown()` renderers,
  replacing `c_type_mapping_markdown()` and `fortran_type_mapping_markdown()`.

- Documentation: added a source-backed Fortran support reference, clarified
  the C direct-wrapper boundary, aligned root CLI help with Fortran, supported
  C, and semantic-`.pyi` inputs, and refreshed the user and contributor
  documentation navigation.

### Fixed

- Fortran-led semantic `.pyi` builds now select the C compiler paired with the
  chosen Fortran driver when no C override is supplied, and record that
  resolved driver for manifest replay instead of forcing the system `cc`.
- Coercive integer callback results now raise `OverflowError` when a Python
  integer falls outside the declared native width instead of narrowing or
  wrapping it silently.
- `UInt64` and `SizeT` scalar results now use the same target-specific NumPy
  scalar identities accepted by their arguments, so a generated result can be
  passed back into the same direct-C API on LP64 targets.
- Manifest replay now validates the recorded semantic `.pyi` import graph
  before generating files or invoking a compiler.
- Mixed-language builds now use the Fortran driver's matching C compiler when
  no C override is supplied, use that same driver for C probing and
  compilation, and reject an explicitly supplied C/Fortran family mismatch.
- Native link-item language requirements now survive result serialization and
  manifest replay for named libraries and linker arguments as well as path
  artifacts, preserving link-driver selection.
- Generated bindings now allocate writable string-replacement buffers only
  after all inputs validate, release every live buffer on later setup or
  conversion failure, free replacements before other fallible output
  conversions, and release unpublished native results if string write-back
  conversion fails.
- Binding-owned array-coercion temporaries now clear their local owner when
  released, so later native-status error cleanup cannot release them twice.
- Failed Python conversion of one native result now releases every later
  unpublished string, array, descriptor, or derived-result owner instead of
  leaking storage returned by the same native call.
- Source builds now fail before native compilation if their promised semantic
  contract package cannot be rendered, and report the written `.pyi` files in
  `WrapperBuildResult.generated_files`.
- Direct-C preflight now rejects every intrinsic unsupported-policy diagnostic
  before target ABI probing; only diagnostics that require compiler-probed
  primitive facts are deferred.
- Direct-C array policy now rejects explicitly non-C layouts instead of
  silently replacing the authored semantic contract with C-order validation.
- Semantic `.pyi` decorators used on declaration kinds where their meaning
  cannot be represented are now rejected instead of silently discarded.
- Abstract derived-type identity is now module-qualified during semantic
  conversion. A concrete type with the same local name in another module no
  longer inherits abstract-dummy policy, while imported abstract types are
  recognized regardless of project source order.

- Source-free C contracts now carry compiler-probed `Int`, `UInt`, and `SizeT`
  storage through primitive arrays and projected outputs while preserving exact
  standard C spellings such as `int *` in generated prototypes. Target-
  generated `int[]` contracts therefore stay in the documented direct-C lane
  without requiring a manual `Int32[:]` rewrite.

- Verbose wrapper builds now print each compiler command before it starts, so
  failed invocations remain directly replayable.

- `semantics` and `generate --pyi` now reject non-source inputs instead of
  emitting an empty report.

- Ordinary array arguments now preserve their non-array type check before
  accessing NumPy storage. Native-handle-capable branches still avoid repeating
  that check after selecting their NumPy fast path.

- Common scalar and string conversions in C bindings with several Python
  outputs now share one linear reference-cleanup path instead of repeating
  every earlier `Py_DECREF` at each failure site. Large wrappers retain the
  same result ownership and diagnostics while generating smaller C
  control-flow graphs.

- Ordinary NumPy-array arguments no longer repeat `PyArray_Check` inside the
  validation helper after the generated fast-path branch has already performed
  that check. Dtype, rank, layout, byte-order, alignment, and mutability
  validation remain unchanged.

- Built-in release compiler profiles no longer force loop unrolling in
  generated wrappers and native sources. Release builds retain `-O3`, and
  callers can still request vendor unrolling flags explicitly; optimized
  large-wrapper builds therefore avoid the hidden compilation cost by default.

- Real Libraries Portability now exposes the matching GNU C driver beside its
  selected GNU Fortran driver. Generated C bindings therefore use GCC on
  macOS, including its `ISO_Fortran_binding.h` search path, instead of
  accidentally resolving Apple's unrelated `gcc`-named Clang driver.

- The copied BLAS and LAPACK examples now give GNU Fortran a positional archive
  input when creating a macOS dynamic library. Apple `ld` still receives the
  targeted `-force_load` option, while the compiler driver no longer aborts
  with "no input files" on either hosted macOS architecture.

- The Linux x86-64 BLAS and LAPACK full-surface CI audits now run in the same
  shell steps as their example builds, so they reuse the temporary extensions
  instead of losing their exported import paths at a GitHub Actions step
  boundary.

- The portable libm tests now read and call `long double` routines through the
  public dtype selected by the target-generated contract. Apple ARM64 uses
  `numpy.float64`, while targets with wider C `long double` storage use
  `numpy.longdouble`.

- An exact native C scalar passed by address and projected back to Python now
  converts its native call-local into the public contract storage type before
  constructing the NumPy result. This removes an incompatible-pointer handoff
  such as `long long *` to an `int64_t` result helper.

- Compiler-preprocessed C prototypes with an unnamed builtin parameter, such
  as Apple `<math.h>`'s `long rinttol(double)`, are no longer mistaken for
  unsupported K&R definitions.

- Compiler-preprocessed C headers that provide fallback `_FloatN` typedefs now
  parse successfully. This keeps private glibc compatibility declarations from
  blocking an allowlisted public API when Clang preprocesses `<math.h>`.

- An exact native C type around a NumPy-backed `Arg(...)` now requires its
  matching NumPy C storage type. For example, `CLongLong(Arg(0))` accepts
  `numpy.longlong` and rejects a distinct `numpy.int64` buffer instead of
  passing that buffer to `long long *` through an incompatible pointer. The
  rule covers all supported exact C types with matching NumPy storage; scalar
  value arguments keep their existing conversion behavior.

- A C translation unit's module variables, enum or macro constants, and
  aggregate type declarations no longer reach wrapper planning. They previously
  generated a Fortran adapter module for a C input and failed with a raw
  compiler error after writing files; they now fail closed before planning with
  `C_DIRECT_NATIVE_GLOBAL_STATE`, `C_DIRECT_ENUM_CONSTANT`,
  `C_DIRECT_MACRO_CONSTANT`, or `C_DIRECT_AGGREGATE_TYPE` and leave no output.

- A C declaration the parser cannot model — for example one carrying an
  unsupported calling-convention attribute — is no longer dropped from a
  wrapper build's public API. It raises `C_DIRECT_UNMODELED_DECLARATION`
  instead of silently publishing a smaller or reinterpreted API.

- `T[:] | None` and `T[()] | None` in a C semantic contract no longer build a
  silently non-nullable wrapper. Nullable C pointers are outside the initial C
  lane, so the contract now fails with `C_DIRECT_NULLABLE_POINTER`.

- A route-neutral `@native_call` reorder in a C contract no longer converts one
  argument's Python value using another argument's declared type.

- An edited array contract can now derive its native extent from the buffer,
  as `@native_call([Arg(0).shape[0], Arg(0)])`. A binding-owned extent, length,
  or presence producer is no longer mistaken for the argument's own transport
  slot, which had also lowered the promoted buffer as a by-value scalar.

- Fortran `bind(C)` procedures that pass strings, derived objects, or callbacks
  through their direct entrypoint build again. The new exact C declaration plan
  is now built only for C-source operations.

- The generated docstring for a call-local scalar address argument no longer
  claims that native code updates the supplied storage in place. That update
  lands in a call-local copy and is not visible in Python.

- A `generate --makefile` build invoked with relative paths now produces a
  Makefile that runs on a clean tree. The link rule demanded each user object
  twice, once under a relative spelling that no rule produced, so `make` stopped
  with "No rule to make target". This affected Fortran and C builds alike.

- C contracts can now pass strings. `String` hands a C `const char *` the
  Python object's own NUL-terminated buffer, and `String[...][()]` hands a
  `char *` a rank-zero NumPy bytes buffer untouched, so native writes are
  visible in place. A declared capacity such as `String[32][()]` additionally
  checks the caller's itemsize. PRIK takes no position on whether the callee
  reads to a terminator or takes a separate length: the contract states which
  form the C code expects. `@raises(message=...)` works too when the projected
  message declares a capacity, such as `Returns["message", String[64]]`: the
  binding owns that buffer and passes it as `char *`, instead of the bridged
  route's owned-allocation `char **`. Arrays of strings, pointer results, and
  owned buffers stay fail-closed.

- `@raises(message=...)` can now name a visible argument instead of a projected
  hidden output, in both the C and Fortran lanes. The caller then supplies
  writable storage — a rank-zero NumPy bytes array for `String[n][()]` or
  `String[...][()]` — so no capacity has to be declared, and the buffer
  survives the raise for inspection. A visible `String` is accepted too, but it
  borrows the Python object's own buffer and lowers to `const char *`: the
  contract states a read-only input, so native code that writes through it is
  violating the declaration it was handed. That is the C API author's call to
  make; prefer NumPy storage for any message the native code fills. Only the
  hidden form still requires a fixed width, because there the binding allocates
  the buffer and the size the native code assumes is not in the signature.

- `Hidden(name, T)` declares a native output the Python signature never shows.
  It is planned, passed, and released exactly like a returned output — the
  bridge sees no difference — and only the binding skips building a Python
  value from it. This makes `@raises` status and message one instance of a
  general mechanism rather than a special case, and it works in both the C and
  Fortran lanes.

- `@raises` targets are now declared with `Hidden(name, T)` inside
  `@native_call` instead of occupying a slot in the return annotation. A status
  or message is produced by the native call but consumed into the exception, so
  listing it as a returned value described a Python signature that never
  existed: `-> tuple[Returns["root", Float64], Returns["status", Int32]]`
  returned a bare `Float64`. Contracts now say what they mean, and the emitted
  `.pyi` normalizes the old spelling to the new one.

- Rank-zero character storage may now leave its width assumed in the Fortran
  lane too: `String[...][()]` takes the width from the caller's NumPy array
  instead of the contract, matching what the C lane already accepted. The same
  now holds for character arrays, where `String[...][:]` takes every element's
  width from the array's itemsize. A declared width still validates the
  caller's itemsize; an assumed one accepts whatever the array carries.

- Rank-zero character storage now always reports its width beside the address,
  so a declared and an assumed width generate the same adapter shape instead of
  baking a literal into the generated Fortran. A raw string address keeps the
  declared width, because a bare caller-supplied address has no Python object
  whose size could be measured.

- A `@raises` message is now read within the capacity its storage declares
  instead of by scanning for a terminator. Fortran blank-pads fixed-length
  character storage and never writes a NUL, so the previous scan reported the
  padding as part of the exception text — a `character(len=64)` message raised
  `'negative'` followed by 56 spaces. When the native code did terminate, the
  bytes are still taken exactly as written.

- A `@private` declaration in a C semantic contract is no longer refused as an
  unsupported C operation. Being unexported is a shared contract feature, not a
  C-lane limit, so the documented `@overload` pattern — private concrete
  candidates behind one public Python name — now works for C.

- A C wrapper build now works when the C compiler is named `cc`. `cc` is the
  documented default for the C lane, but its vendor was read from the
  executable's filename, which names no vendor. That happened to work where
  `cc` links to a vendor-named binary and failed everywhere it does not, such
  as macOS. The driver's own `--version` banner now settles the vendor when the
  name cannot.

- The BLAS and LAPACK examples now expect the character selectors that the
  conservative `intent(inout)` default returns. Their assertions still encoded
  the older `intent(in)` assumption for `character` dummies, so the example
  suites failed against the behavior the same release documents. Positional
  reads of a returned scalar tuple moved with the selectors; five LAPACK
  assertions that had kept passing on a coincidentally equal value now index
  the dummy they name.

- The semantic contract a C build saves beside its extension now describes only
  the wrapped file's own API. Preprocessed system-header declarations stay
  inspection facts instead of filling the contract with private entries that
  the next build could not accept.

- A C parameter or result written through a typedef now declares the exact
  builtin type the compiler probe resolved it to. The generated binding writes
  its own prototype, so a typedef name defined only by the wrapped source's
  headers previously reached the compiler undeclared and failed the build after
  files were written.

### Added

- Added a portable libm example that regenerates its target-specific semantic
  `.pyi` from a reviewed 60-function ISO C99 `math.h` selection before every
  build and validates every exported routine with a named numerical test. The
  contract records exact native scalar casts without changing its NumPy-facing
  signatures, and its dtype assertions follow the active `long` and `long
  double` ABIs. A dedicated Real Libraries Portability workflow, reused by the
  pull-request gate, runs all maintained examples on Linux x86-64, Linux Arm64,
  macOS Intel, and macOS Arm64; libm additionally runs with GCC and Clang on
  each platform, and Linux x86-64 retains the deep BLAS and LAPACK audits.

- `--positional-only` exposes every wrapper whose arguments are all required as
  positional-only, renaming them `arg0`..`argN` in the signature, docstring, and
  argument diagnostics. A native declaration's parameter names then stay out of
  the Python API, which matters for a system header that spells them `__x` or
  omits them entirely. A function with an optional argument keeps its keywords,
  and a module with overload sets is rejected because overload dispatch selects
  a candidate by keyword.

- `--lto` adds `-flto` to generated and native compilation and to the extension
  link. A collision adapter is emitted with hidden visibility, so link-time
  optimization can inline the forwarder and drop its definition rather than
  exporting it from the extension.

- Target-specific C contracts now preserve exact scalar call identities with
  sparse expressions such as `CLongLong(Arg(0))` and typed native-result
  projections. Public annotations remain ordinary NumPy types; policy completes
  the conversion before planning and the binding reuses its exact native scalar
  storage and direct-result path. Native C scalar names are rejected outside
  `@native_call`.

- `--collision-adapter NAME` and `--collision-adapter-all` now isolate genuine
  C identifier collisions only. The separate translation unit includes no
  `Python.h`, reconstructs the completed exact native declaration, and emits a
  hidden pure forwarder defined once per native symbol even when several Python
  callables name it. Only a C-source function is eligible: an explicitly named
  symbol that is unknown or ineligible fails before wrapper planning, while
  `--collision-adapter-all` passes over Fortran `bind(C)` entrypoints instead
  of failing the build. Saved build manifests retain the selected adapter mode
  when replayed.

- Added a published C support guide with executable source and semantic-contract
  workflows, CLI and Python build APIs, supported primitive and NumPy-pointer
  contracts, compiler preprocessing, and the direct lane's fail-closed limits.
  Published the linked language-support, CLI, Python API, diagnostic, reference,
  and examples landing pages after aligning their commands and public links with
  the implemented surface.

- Added the initial direct-only C wrapper lane. `build_c_extension`, explicit
  `native_c_sources`, and C-native semantic `.pyi` contracts compile, link,
  import, and call supported target-probed primitive C symbols directly. The
  lane covers arithmetic scalar values, `void`, completed scalar-reference and
  primitive NumPy-pointer contracts, and fails closed before planning for
  callbacks, aggregates, variadics, pointer results, multi-level or nullable
  pointers, ownership-sensitive forms, and other unsupported C ABI features.
  C wrapper builds preprocess their sources with the selected C compiler, so an
  ordinary `#define`, `#ifdef`, or macro-defined declaration is read the same
  way the C inspection routes read it, and only the wrapped translation unit's
  own declarations become public API.

- Every build now writes its semantic `.pyi` contract beside the extension, in a
  `contracts/` package inside the build directory (`__prik__/contracts/` by
  default). Reshaping the generated Python API no longer needs a separate
  `generate --pyi` run: the contract describing the API a build just produced is
  always there, and rebuilding from it works directly. It lives in its own
  directory so its `__init__.pyi` cannot make the build directory look like a
  Python package.

- Generic constructors declared as `interface <typename>` are now wrapped from
  Fortran source. Such an interface is that type's constructor, so its specifics
  become the accepted signatures of one overloaded `__init__` rather than a
  module-level generic, and a call matching none of them is refused instead of
  guessed at. A specific that is `private` in its module is reached through the
  public type name, which resolves to the same procedure. Because the interface
  supplies every accepted signature, it replaces the keyword-field constructor,
  and the generated contract states only the signatures the class accepts. The
  three sources of a constructor are now: no user constructor keeps the
  keyword-field `__init__`, an `interface <typename>` supplies the overload set,
  and an edited `.pyi` declares exactly what it says. A constructor candidate
  carries no `@bind`, because the class name already states the generic that
  reaches it — the same reason an unrenamed method omits it — and `@private` is
  refused on `__init__`, since a constructor is published or absent and the
  accessibility of the specific it selects is that procedure's own fact.

- Added the BSPLINE-FORTRAN example under `examples/fortran/bspline`. It wraps
  the upstream sources unmodified and validates both public interfaces from
  Python: the object-oriented classes over an abstract base with deferred
  bindings and generic constructors, and the procedural interpolation
  routines. Numerical checks use analytic values and `scipy.interpolate` as
  independent oracles. It is the first example project written in modern
  Fortran rather than FORTRAN 77.

- BSPLINE-FORTRAN now follows the maintained real-library example workflow:
  its checked-in build instructions are verified with the documentation suite,
  its full procedural and derived-type surface is exercised in the native
  library CI job, and its inventory fails closed if generated exports or named
  numerical tests drift. The example now calls all one- through six-dimensional
  procedural setup and evaluation routines and constructs every concrete spline
  class against an independent affine interpolation result.

- Abstract Fortran derived types are now wrapped. A `type, abstract ::`
  declaration becomes a Python class with no constructor — instantiating it
  raises `TypeError` naming the concrete extensions to use instead — while its
  extensions remain ordinary Python subclasses that inherit its implemented
  bindings. A deferred binding (`procedure(iface), deferred ::`) is declared on
  the base and resolved by the object's own type: the generated adapter converts
  the address to the caller's concrete type and lets Fortran select the
  override, so no Python-side dispatch is involved. An abstract type publishes
  no component accessors of its own, because each extension already generates
  one for every component it inherits, and it is excluded from the polymorphic
  cases a caller can supply, since no object can have it as a dynamic type. In
  semantic `.pyi` contracts the class carries `@abstract` and each deferred
  binding carries `@abstractmethod`, both re-exported from `prik.contracts`;
  a deferred binding never carries `@bind`, because it has no native symbol.

### Changed

- Reorganized the C and Fortran test suites around a strict ownership rule:
  language features remain under `<feature>/<stage>`, while shared parsing,
  preprocessing, CLI, semantic-representation, contract, build, and policy
  evidence live under `infrastructure/`. Focused commands and documentation now
  use the corresponding infrastructure owners.

### Fixed

- A `bind(C)` character dummy that is a pointer now declares deferred length,
  as the Fortran standard requires. GNU Fortran 13 and newer reject the
  declared-length spelling earlier releases emitted, so wrapping a
  `character(len=N), pointer` module array failed to compile there. Pointer
  assignment takes the length from its target, so the associated width is
  unchanged. The matching allocatable descriptor consumer travels as an
  assumed-length assumed-shape dummy, whose descriptor still carries the
  element length.

- A generic interface whose specifics project an `intent(out)` argument into a
  result now reloads from its generated contract. The declaration states the
  public signature, so an output the projection turned into a result is not one
  of the arguments it accepts; comparing the declaration against the specific's
  native argument list rejected every such generic — the common shape in
  numerical Fortran — with "Overload declaration 'x' is incompatible with
  specific procedure 'y'". The same comparison now drives a type-bound generic's
  receiver search. Generated contracts for BSPLINE-FORTRAN's `db1ink`,
  `db1val`, and `initialize` load again.

- A module whose only procedures are `bind(C)` now installs the bundled native
  support its derived-type accessors need. Compiled wrapper builds for such a
  module previously failed to link with `undefined symbol:
  prik_float64_to_numpy`, because native support was requested only for module
  variables, for ordinary procedure arguments and results, and for array
  components — and a `bind(C)` procedure supplies none of those. Every published
  component converts through those helpers, so a type with any component now
  requests them.

- A derived type's `private` and `public` statements are now honored. The
  statement before `contains` sets the default accessibility of components and
  the statement after it sets the default for type-bound procedures; a
  declaration that states its own accessibility still keeps it. The statement
  after `contains` previously failed to parse at all, and the one before it
  parsed but was discarded — so a type with private components reached the
  Fortran compiler as generated accessors that read them, failing with
  "Component 'x' is a PRIVATE component of 'y'". Private components and
  bindings now simply stay off the generated Python class. Parsed derived types
  additionally record `component_visibility` and `binding_visibility`, and each
  type-bound binding records the `visibility` it resolves to, so the parser's
  serialized form states the accessibility it read.

- A `type, public ::` declaration is no longer hidden by a module-level
  `private` default. The type's own declared accessibility is the most specific
  statement about it, so it wins over the module default and over the module's
  accessibility lists. Previously such a type — and every one of its methods —
  was dropped from the extension silently, with the build still reporting
  success.

- A deferred type-bound binding (`procedure(iface), deferred :: name`) now
  parses instead of failing as a syntax error, so whether it can be wrapped is
  a policy decision rather than a parser limit. Abstract types and deferred
  bindings are wrapped as described above; this entry records only the parsing
  change that made that possible.

- A named `block` construct (`main: block ... end block main`) is recognized as
  the start of a procedure's execution part. A construct name prefix is now
  stripped before a statement is classified, so named `do`, `if`, `select`,
  `associate`, and `block` constructs are all read as executable rather than as
  an unknown declaration.

- The compiler type probe no longer emits a program it cannot compile. The
  probe is a standalone program that cannot `use` a module from the project
  being analyzed, because that module has not been compiled yet; an expression
  naming a kind parameter declared elsewhere in the project — `storage_size(1_ip,
  kind=ip)`, for example — is now left for the requirement report instead of
  being compiled into the probe. Previously one such expression failed the whole
  probe and with it the entire build.

### Added

- Added the C-only `--export-symbols FILE` allowlist for source builds,
  `semantics`, and `generate --pyi`, with resolved-name parity through
  `build_c_extension(export_symbols=...)`. It promotes exactly the named
  reachable functions even from private system headers, excludes every
  unlisted declaration, and fails closed for malformed, repeated, missing,
  non-function, or ambiguous selections. This lets maintained examples parse
  platform headers without publishing their implementation-specific surface.

- The libm portability audit now reuses the Linux x86-64 and macOS Arm64 CI
  jobs and adds one focused Linux Arm64 job. All three regenerate from the
  target `math.h` and run the complete 60-function suite without repeating the
  heavyweight Fortran real-library matrix.

- The libm example now stops immediately when contract generation or wrapper
  compilation fails, instead of exporting a broken build environment to a
  later test command.

- Added `--assume-intent-in-scalars`, which treats a primitive scalar dummy
  that declares no `intent` as `intent(in)` instead of applying the
  conservative `intent(inout)` default. Fortran permits an undeclared dummy to
  be written, so prik returns its post-call value; for sources that predate the
  `intent` attribute this fills the Python return with unmodified controls, and
  reference BLAS `ddot` returns `(value, n, incx, incy)` rather than the value
  alone. With the option, that call returns `32.0`. The choice is made once in
  semantic conversion, where an absent `intent` is interpreted, so the build
  and `generate --pyi` describe the same Python surface. It is deliberately
  narrow: it covers the primitive and character scalars whose replacement is
  otherwise returned, a declared `intent` always wins, and arrays,
  derived-type objects, and allocatable or pointer scalars are unaffected. It is an
  assertion about the source rather than a fact derived from it — prik does not
  inspect the procedure body, so a procedure that does write such a dummy
  loses that value, exactly as removing the result from the generated contract
  by hand would. The option appears in the first `--help` screen because it
  changes the default Python surface, and every command that produces semantic
  IR accepts it — the build, `generate --pyi`, and `semantics`.
  `--build-manifest` rejects it along with the other saved wrapper settings,
  and a `.pyi` wrapper build rejects it because a contract already states its
  own results.

### Changed

- A scalar `character` dummy that declares no `intent` now uses the same
  conservative `intent(inout)` default as every other scalar, so the value the
  native procedure left behind is returned. It was silently assumed
  `intent(in)`, which meant a procedure that wrote to such a dummy lost that
  write with no diagnostic, while an `integer` dummy on the same call had its
  write returned. The exception was undocumented and untested; the strings
  guide already stated the uniform rule this change makes true. Wrapping
  fixed-form sources, where `intent` cannot be declared, therefore returns
  `(result, text)` where it previously returned `result` —
  `--assume-intent-in-scalars` restores the shorter surface and now covers
  character scalars along with primitive ones. An `allocatable` or `pointer`
  character scalar with no `intent` likewise now matches its numeric
  counterpart and returns a nullable snapshot; the option does not reach either
  one, because a snapshot is not a replacement value the caller supplied.

- Generated wrapper source is now readable. Each generated Fortran adapter and
  each CPython binding function carries a short leading comment naming what it
  is for — the native procedure an adapter wraps and the C symbol it exports,
  the Python callable a binding serves and the entrypoint it calls, and what a
  module accessor reads or writes — and an adapter additionally summarizes the
  conversions it performs. Generated Fortran modules also separate their
  procedures with a blank line instead of running them together. Comment prose
  is wrapped well inside the free-form 132-column limit, and each backend
  describes only its own plan facet, so the binding never names a Fortran
  symbol and the bridge never names a Python one.

### Fixed

- Declared-length `character` module arrays (`character(len=4), allocatable ::
  arr(:)`, and the `pointer` equivalent) no longer fail in the Fortran
  compiler. The generated descriptor-consumer interface and descriptor ABI
  parameter both spelled `character(len=:)` regardless of what the array
  declared, and an allocatable or pointer dummy accepts a deferred-length
  actual only when it declares one itself. Both now spell the declared width.
  A deferred-length `character(len=:), allocatable` module *array* still fails
  to compile under GNU Fortran 11.4 with an internal compiler error, which is a
  compiler defect rather than a wrapper contract.

### Added

- Every `character` module-variable form is now wrapped. Declared-length
  scalars are readable and writable as ordinary `str` properties, matching how
  numeric module variables already behave; a character value has no by-value C
  ABI, so the accessors copy through the same fixed-width buffer a character
  field already used, and assignment requires exactly the declared byte width
  rather than truncating or padding. `allocatable` and `pointer` scalars read
  as a detached `str`, or `None` when unallocated or unassociated, through the
  same nullable snapshot a descriptor numeric scalar uses, carrying the width
  the descriptor holds at the time of the read. `character` `parameter` arrays
  are copied once at import into a read-only fixed-width bytes array, the way
  numeric parameter arrays already were. Character module arrays report their
  own element width through their generated accessor rather than having it
  restated by the binding, so an assumed-length (`character(len=*)`) parameter
  array works too and takes the dtype width its initializer implied. An
  assumed-length scalar still keeps its rejecting setter, having no storage
  width to write into.

- Fixed-shape `character` module arrays with the `target` attribute now expose
  the same live fixed-width bytes view numeric module arrays already did, at
  any rank. The live-view lane rejected them only because it required a
  primitive numeric element type; a character element differs only in carrying
  its Fortran element length as the dtype width. Native writes appear in the
  view, and Python writes reach the storage Fortran reads. `target` is required
  here exactly as it already was for numeric module arrays.

- Pointer array handles now expose `deallocate()` without a `PointerPolicy`
  annotation, matching what allocatable handles already offered. Release stays
  manual and caller-driven — prik never frees a native target on its own, on
  garbage collection or otherwise — so this is the same responsibility a
  Fortran caller takes when writing `deallocate` for the same pointer.
  Previously a wrapped procedure that returned freshly allocated pointer
  storage leaked with no way to reclaim it from Python. `allocate` and `resize`
  still require `PointerPolicy`, because they establish a new target rather
  than releasing the one the handle already names.
- Added wrapper support for `allocatable` and `pointer` scalar `character`
  values in every direction: `intent(in)`, `intent(out)`, and `intent(inout)`
  arguments, and function results, at both deferred (`len=:`) and declared
  (`len=n`) length. Policy now completes the adapter-local storage each dummy
  needs — its attribute, its length, and who releases it — instead of always
  building a plain fixed-length temporary. The C ABI is unchanged: a scalar
  character argument still crosses as a byte buffer and a length whatever the
  dummy declares. Previously most of these forms either stopped at a policy
  diagnostic or reached the Fortran compiler and failed there with
  "Actual argument for 'x' must be ALLOCATABLE"; declared-length allocatable
  and pointer forms additionally failed plan validation.
- Added a character-length subscription to semantic `.pyi` contracts. The first
  subscription after `String` is always the length — `String[...]` assumed,
  `String[8]` or `String[n]` explicit, `String[:]` deferred — and an array adds
  its shape as a second subscription. Deferred-length scalars therefore have a
  contract spelling for the first time, so those procedures rebuild from their
  generated contract; the one-subscription array spellings the printer used to
  emit (`String[::]`, and `String[n]` for an extent) are replaced by
  `String[...][::]` and `String[...][n]`, which the parser had rejected or read
  as a scalar length.
- Added wrapper support for mutable scalar character descriptor arguments
  (`allocatable` or `pointer`, `intent(inout)`). The dummy stays a `str`
  argument and additionally returns the value the native procedure left behind,
  or `None` when it leaves the dummy unallocated or unassociated. Policy
  completes two decisions for the one dummy — a call-local character-buffer
  input and a nullable descriptor result — so the adapter copies back the local
  the native procedure may have replaced rather than the caller's buffer. A
  pointer dummy additionally records who releases the target the adapter
  allocated: the adapter frees it only while the dummy still identifies it, so
  storage the native procedure deallocated or replaced is left alone. The dummy
  spells as `Allocatable(Arg(i))` or `Pointer(Arg(i))` with `String[:]` or
  `String[n]` in a semantic `.pyi` contract, so these procedures also rebuild
  from their generated contract.
- Added wrapper support for `allocatable` scalar `character` function results.
  The adapter moves the result out through an allocatable dummy rather than
  assigning it, which makes allocation a testable fact, so an unallocated
  result becomes `None`. Other allocatable scalar function results remain
  blocked, because they have no such completed move.
- Added `@native_abi("c")` to semantic `.pyi` contracts so Fortran `bind(C)`
  procedures retain their ABI and optional link label through generated and
  source-free contract workflows.
- Added selective direct routing for policy-proved Fortran `bind(C)` procedures,
  including direct/mixed compiled feature fixtures and support-only generated
  Fortran artifacts where independent helpers remain necessary.
- Added a separate direct-entrypoint PRIK/f2py runtime and clean-build benchmark
  cohort with untimed correctness, generated-source membership, and linked
  direct-symbol preflight, plus an ordinary-Fortran PRIK control.

### Changed

- Made nested semantic classes use the same complete planning and backend-symbol
  allocation path as top-level classes.
- Published the maintained-run direct-entrypoint runtime, adapter-control, and
  clean-build results separately from the normal-interface benchmark cohort.
- Made direct-entrypoint benchmark preflight identify binding and native
  objects by their inspected symbol relationships across f2py build backends.
- Reduced exact numeric-scalar call overhead by using typed NumPy scalar
  payload access and result allocation while preserving strict dtype checking
  and exact NumPy result types.
- Separated wrapper plans into strict binding, shared native-entrypoint, and
  Fortran-adapter facets, with planner-owned generated support procedure
  entrypoints for accessors, lifecycles, descriptors, and callbacks, without
  changing generated wrappers.
- Build manifest schema 4 records physical generated sources and separate
  adapter/support membership, including zero-generated-native builds.

## 0.3.0 — 2026-08-14

### Added

- Reorganized contributor documentation around a concise architecture guide
  and one canonical page per production package, with local structures,
  important objects, runnable examples, expected outputs, test owners, change
  routes, and invariants.
- Consolidated contributor workflows and removed nonessential concept and
  design drafts, TODO-only pages, duplicate architecture maps, and completed
  migration ledgers.
- Added the persistent Zenodo all-versions DOI badge and citation links to the
  README and About page.
- Included the repository's machine-readable `CITATION.cff` metadata in source
  distributions.

### Changed

- Marked the contributor Architecture and Codebase Map as reviewed for
  publication; the renamed map now focuses on package and cross-stage module
  ownership.
- Clarified the Feature-to-Code Map as the capability-to-owner and evidence
  index, linking reviewed user documentation and retaining only planned
  contributor-documentation paths before their review.
- Revised the Feature-to-Code Map with reviewed package-guide links,
  stage-ordered change routes, narrower focused evidence, and separate array,
  callback, and error routes.
- Condensed the contributor Testing Strategy around test ownership, stage
  evidence, stable contracts, end-to-end evidence, fixture placement, and
  verification scope.
- Clarified contributor workflows for changing PRIK, local verification, pull
  request checks, and documentation maintenance.
- Linked the Contributing workflow to the Feature-to-Code Map and Testing
  Strategy, explained its pre-push hook setup, and normalized its editable
  checkout test commands.
- Clarified that pull-request validation requires the performance benchmark and
  identified its workflow implementation.
- Renamed the Package Guides section to Architecture Components and grouped its
  build stages separately from its supporting components, distinguishing
  cross-build pipeline orchestration from sequential stages.
- Ordered the Developer Documentation sidebar by the architecture reading path,
  with build stages before supporting components.
- Made every expandable documentation-sidebar section label open its first
  published page, including through nested sections, while the adjacent **+**
  control only expands or collapses it.
- Made documentation tables wrap readable cell content instead of hiding
  later columns behind unnecessary horizontal scrolling.
- Added accessible two-, three-, and four-view example tabs to the User Guide;
  Getting Started remains linear and example results stay visible.
- Reviewed the Pipeline Component guide around the source-build handoff,
  independent contract and inspection workflows, and build-result ownership.
- Reviewed the Preprocessing Stage guide around its Fortran source route,
  compiler-derived target probes, module navigation, and executable examples.
- Reviewed the Parsing Stage guide around its Fortran and semantic-`.pyi`
  algorithms, source-level navigation, executable examples, and ownership
  boundaries.
- Reviewed the Semantics Stage guide around its shared IR, frontend-conversion
  algorithms, raw contract facts, executable examples, and policy boundary.
- Reviewed the Policy Stage guide around ordered policy completion, immutable
  interoperability decisions, module algorithms, executable examples, and the
  planning boundary.
- Reviewed the Planning Stage guide around deterministic policy projection,
  editable plan ownership, module algorithms, executable examples, and the
  generator freeze boundary.
- Reviewed the Code Generation Stage guide around its generator handoff,
  backend lowering algorithms, plan-only decisions, executable examples, and
  focused evidence.
- Reviewed the Printing Stage guide around representation-specific traversal,
  safe source formatting, isolated `.pyi` emission, executable examples, and
  focused evidence.
- Reviewed the Compiler Stage guide around coherent toolchain selection,
  explicit command construction, conditional native-support installation,
  executable examples, and focused evidence.
- Added focused C Binding and Fortran Bridge lowering guides with executable
  manually constructed plans and printed backend-source examples.
- Moved binding and bridge algorithms and rendered-source demonstrations out
  of the Code Generation overview and into their focused lowering guides.
- Explained each reviewed package-guide execution example in terms of its
  in-memory setup and the stage boundary established by its output.
- Added Pipeline Component and source-level navigation for contract loading,
  wrapper generation, build-manifest replay, and `build.py` orchestration.
- Removed empty package-marker entries from the Pipeline Component and Compiler
  Stage guides.
- Added a brief Developer Documentation overview that routes readers to
  Architecture, then Architecture Components, and linked it from the website
  home page.
- Replaced the contributor architecture's text-only build path with a rendered
  diagram of its two input routes and shared pipeline.
- Made the architecture build-path diagram keyboard-accessible and linked each
  route and stage to its reviewed component guide.
- Added accessible explanations for `.pyi`, f2py `.pyf`, ABI, semantic IR,
  array order, and the GIL throughout User Documentation and on the Home page,
  plus per-stage detail panels to the architecture diagram.
- Changed the site-wide repository control into a “★ Star on GitHub” call to
  action while preserving its repository destination.
- Published concise Contracts, Naming, Runtime, and Utilities component guides,
  restored their architecture links, corrected the diagram fallback, and
  clarified the NumPy result type in the architecture example.
- Made numeric scalar results consistently preserve their exact NumPy types;
  Boolean scalar results remain Python `bool` values.
- Corrected user documentation to distinguish numeric and Boolean scalar
  boundaries, and aligned the Getting Started route with normal package
  installation rather than a repository checkout.
- Reduced documentation tests to enforce publication, link integrity,
  executable examples, and public-reference contracts without freezing prose,
  headings, page inventories, private names, or source-tree layout.
- Reclassified implementation-structure and codegen-complexity checks as
  contributor recommendations, while retaining hard behavioral, safety, ABI,
  publication, and architectural-boundary contracts.
- Moved contributor package-guide execution checks into the documentation
  suite, using each guide's displayed result instead of a duplicate exact-
  output inventory.
- Reduced the root `prik` API to its version and normal-user build entrypoints;
  parser, semantic, probe, runtime, and planning tools now use their owning
  package import paths.
- Moved stage-record freezing from `prik.stage_values` to
  `prik.utilities.stage_values`; the root module path was removed.
- Made `prik` an import-only package boundary by removing its direct-script
  demonstration; command and stage-value examples remain available from their
  owning modules.
- Expanded the contributor architecture and package guides with concrete stage
  handoffs, runnable example results, focused test purposes, and change routes.
- Moved generated documentation and distribution output under the hidden
  `.artifacts/` directory in local commands and CI workflows.
- Consolidated developer and maintainer material under one Contributor
  Documentation tree and removed the separate maintainer documentation lane.
- Moved the bundled header-only binding runtime from the package root into
  `prik.runtime.native_support`; generated builds continue to receive it under
  their internal `binding_support/` include directory.
- Deferred the contributor architecture sections for the immature C input
  parser and C-to-IR path while retaining the generated CPython C binding
  backend documentation required by Fortran wrappers.
- Reorganized compiler and pre-parse infrastructure into `prik.compiler` and
  `prik.preprocessing`, including C/Fortran preprocessing and target probes;
  the former `prik.compiling`, `prik.probes`, parser-local C preprocessor, and
  pipeline-local preprocessing import paths were removed.
- Replaced the public semantic-to-NumPy helper API with stage-owned semantic,
  contract-runtime, and code-generation datatype catalogues.
- Separated post-IR policy and wrapper planning into `prik.policy` and
  `prik.planning`; code generation now renders plan-driven docstrings, and the
  former maintainer import paths were removed.
- Added a top-level language-printer package for C, Fortran, and semantic
  `.pyi` output, and made `pipeline.wrapper.WrapperGenerator` the single
  plan-to-rendered-wrapper orchestration boundary.
- Documented the completed ownership vocabulary, lifetime-policy philosophy,
  pointer-policy boundary, and maintainer change routes in one maintained
  architecture reference.
- Moved exact overload selection from generated Python predicate chains to
  generated C dispatchers with planned candidate IDs and direct switch-based
  calls to the selected existing wrapper.
- Stopped standalone Fortran parser discovery from descending into inaccessible
  procedure-internal subprograms; procedure-local callback interfaces remain
  classified and discoverable.
- Made directory project parsing read and parse each discovered Fortran file
  once before dependency ordering and project assembly.

### Fixed

- Corrected README licensing wording to refer to bundled native-support files
  rather than the removed package-root `binding_support/` path.
- Unified source-level compile-time resolution across project and CLI parsing
  so imported and host-associated kind facts also reach derived-type fields.

## 0.2.1 — 2026-08-11

### Added

- Added machine-readable citation metadata through the repository-root
  `CITATION.cff` file.
- Added an About page and public development disclosure covering PRIK's
  motivation, design principles, stewardship, and use of AI-assisted tools.

### Fixed

- Removed the stale `0.1.x` qualifier from the README and website alpha-status
  wording after the `0.2.0` release.

## 0.2.0 — 2026-08-10

### Added

- Added maintained FFTPACK and MINPACK examples built from the upstream
  fortran-lang projects. Their build scripts, user guides, and numerical tests
  cover all 31 FFTPACK and 22 MINPACK public procedures.
- Added Python-owned, read-only NumPy snapshots for supported public Fortran
  parameter arrays, including MINPACK's `dpmpar` constants.
- Added declaration-expression support for richer arithmetic, comparisons,
  conditionals, array inquiries, and local, imported, or standalone
  specification functions, including native-dependent result extents.
- Added exact NumPy Boolean-array conversion for compiler-measured 8-, 16-,
  32-, and 64-bit Fortran logical kinds, with canonical writeback.
- Added `WrapperBuildResult.import_module()` to load a generated extension
  explicitly without changing `sys.path`.

### Changed

- Moved documentation and maintainer-tool tests to `tests/docs/` and
  `tests/tools/`, removed the generic `tests/shared/` bucket, and mirrored
  internal tests by production package with narrower support helpers; removed
  recursive layout-policing tests that froze maintainer organization, retaining
  exceptional release safety under `tests/workflows/`. The maintainer-tool and
  workflow-safety suites, blocking static analysis, and focused documentation
  smoke checks now also run through the repository's tracked pre-push hook,
  together with one compiled scalar-wrapper smoke test, for earlier local
  feedback while remaining enforced by GitHub Actions.
- Simplified the documented DGESV validation and the LAPACK test suite to use
  explicit NumPy Fortran-order copies, with documented numerical-test helper
  conventions.
- Aligned the documented MINPACK `hybrd1` callback example with its runnable
  test, made it verify callback invocation, and made its test problems
  self-contained; FFTPACK workspace initializer tests now validate a paired
  transform against NumPy or SciPy.
- Renamed the developer-facing wrapper generation package from
  `prik.wrapper_codegen` to `prik.codegen`; the old import path was removed.
- Expanded public interface resolution so implemented unnamed interfaces and
  public generics can be wrapped without exposing private implementation
  procedures.
- Expanded the Real Libraries CI lane to build and test BLAS, LAPACK, FFTPACK,
  and MINPACK, with cached native BLAS and LAPACK builds where available.
- Made performance comparisons faster and less order-sensitive with balanced
  A/B/B/A runtime measurements, merged samples, smaller worker budgets, and
  four measured clean builds after warm-up.
- Refreshed the README and website around the canonical
  **PRIK — Python Runtime Interop Kit** identity, with a concise FAQ, a fair
  PRIK-versus-f2py guide, clearer array guidance, and searchable real-library
  examples, including a four-library capability and validation summary, a
  concise statement of current limitations, and a derived-type inheritance
  walkthrough.
- Hardened preprocessing, compiler-derived type probes, semantic policy
  completion, and multi-source build reporting so unsupported contracts fail
  earlier with clearer diagnostics.

### Fixed

- Preserved authoritative public interface signatures when linked legacy
  implementations use different internal storage declarations, including
  FFTPACK's `zfftf` complex-array interface.
- Corrected SciPy reference inputs for the LAPACK `dstemr` and `dstebz` tests
  and strengthened BLAS and LAPACK routine validation with independent
  mathematical expectations.

## 0.1.1 — 2026-08-03

- Update README and CONTRIBUTING
- Change the Description section and add more tags


## 0.1.0 — 2026-08-03

- First public release under the PRIK name.
- Build importable Python extensions from supported Fortran sources.
- Generate, inspect, edit, and rebuild from semantic `.pyi` contracts.
- Expose the `prik` console command and the equivalent `python -m prik`
  module command.
- Report the installed release through `prik --version` and
  `prik.__version__`.
- Added a complete runnable Reference BLAS correctness example covering all 155
  discovered routines through PRIK, independent mathematical expectations, and
  f2py differential comparisons.
- Moved the repository's authoritative Reference BLAS sources to
  `examples/fortran/blas/native/` for shared use by the example, integration
  tests, LAPACK CI build, and build comparison tooling.
- Added a complete Reference LAPACK build and correctness project. It wraps all
  2,062 implementation sources once and explicitly validates the reviewed 127
  SciPy 1.18.0 double-precision real routines against independent mathematical
  invariants and f2py comparisons in the dedicated CI lane.
- Moved the repository's authoritative Reference LAPACK implementation sources
  to `examples/fortran/lapack/native/` and updated full-library integration and
  CI to consume that single source owner alongside
  `examples/fortran/blas/native/`.
- Fixed dependency-safe Python argument conversion ordering for wrappers whose
  array extents depend on later native scalar arguments, including padded BLAS
  leading dimensions.
