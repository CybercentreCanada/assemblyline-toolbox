

# Assemblyline toolbox

Bindings for rust components to be exposed to python.

## Repo status

This package is separated from the other assemblyline rust components as the `maturin` toolchain it is using comes bundled with action hooks for github which our main build pipeline doesn't use. While these bindings are under development, or until those actions are ported to our main pipeline, this repo can be used to build python packages that can be _version pinned_ in the assemblyline python packagaes.

_This does mean that the rust code available to python packages will be slightly out of step and require manual builds on this repo to update._

