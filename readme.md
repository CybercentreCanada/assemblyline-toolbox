

# Assemblyline toolbox

Bindings for rust components to be exposed to python.

## Repo status

This package is separated from the other assemblyline rust components as the `maturin` toolchain it is using comes bundled with action hooks for github which our main build pipeline doesn't use. While these bindings are under development, or until those actions are ported to our main pipeline, this repo can be used to build python packages that can be _version pinned_ in the assemblyline python packagaes.

_This does mean that the rust code available to python packages will be slightly out of step and require manual builds on this repo to update._

# Assemblyline toolbox

Liaisons permettant d'exposer les composants Rust à Python.

## État du dépôt

Ce paquet est séparé des autres composants Rust d'Assemblyline parce que la chaîne d'outils `maturin` qu'il utilise intègre des hooks d'action pour GitHub, que notre pipeline de construction principal n'utilise pas. En attendant le développement de ces liaisons ou leur intégration à notre pipeline principal, ce référentiel permet de créer des paquets Python dont la version peut être fixée dans les paquets Python d'Assemblyline.

_Cela signifie que le code Rust disponible pour les paquets Python sera légèrement décalé et nécessitera des mises à jour manuelles sur ce dépôt._
