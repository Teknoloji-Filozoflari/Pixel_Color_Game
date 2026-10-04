{ pkgs ? import <nixpkgs> { } }:
pkgs.callPackage ./packaging/nix/package.nix { }
