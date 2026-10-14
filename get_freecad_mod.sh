#!/usr/bin/env bash
# Определяет путь к каталогу Mod установленного FreeCAD (Linux).
#
# Использование:
#   ./get_freecad_mod.sh             — напечатать путь к .../FreeCAD/Mod (exit 1, если не найден)
#   ./get_freecad_mod.sh --create    — то же, но создать каталог, если не найден
#   ./get_freecad_mod.sh --prefix    — напечатать корень данных .../FreeCAD (без /Mod)
#
# Приоритет:
#   1. env FREECAD_MOD_DIR (явное переопределение)
#   2. первый существующий из кандидатов:
#        $XDG_DATA_HOME/FreeCAD/Mod  (по умолчанию ~/.local/share/FreeCAD/Mod — FreeCAD 0.20+, deb/AppImage/своя сборка)
#        ~/.FreeCAD/Mod              (старые FreeCAD < 0.19)
#        ~/.var/app/org.freecadweb.FreeCAD/data/FreeCAD/Mod  (Flatpak)
#        ~/snap/freecad/current/.local/share/FreeCAD/Mod    (Snap)
#
# Пример явного переопределения:
#   FREECAD_MOD_DIR=/opt/freecad/Mod make cp-plugin-to-freecad

set -euo pipefail

XDG_DATA="${XDG_DATA_HOME:-$HOME/.local/share}"

CANDIDATE_MODS=(
    "$XDG_DATA/FreeCAD/Mod"
    "$HOME/.FreeCAD/Mod"
    "$HOME/.var/app/org.freecadweb.FreeCAD/data/FreeCAD/Mod"
    "$HOME/snap/freecad/current/.local/share/FreeCAD/Mod"
)

CREATE=0
PREFIX=0

die() {
    printf 'get_freecad_mod.sh: %s\n' "$*" >&2
    printf 'Задайте путь вручную: FREECAD_MOD_DIR=/путь/до/Mod make cp-plugin-to-freecad\n' >&2
    exit 1
}

parse_args() {
    local arg
    for arg in "$@"; do
        case "$arg" in
            --create) CREATE=1 ;;
            --prefix) PREFIX=1 ;;
            *) die "неизвестный аргумент: $arg" ;;
        esac
    done
}

print_result() {
    local mod_dir="$1"
    [ "$PREFIX" = "1" ] && { printf '%s\n' "${mod_dir%/Mod}"; return 0; }
    printf '%s\n' "$mod_dir"
}

find_mod_dir() {
    local candidate

    if [ -n "${FREECAD_MOD_DIR:-}" ]; then
        [ "$CREATE" = "1" ] && mkdir -p "$FREECAD_MOD_DIR"
        print_result "$FREECAD_MOD_DIR"
        return 0
    fi

    for candidate in "${CANDIDATE_MODS[@]}"; do
        [ -d "$candidate" ] || continue
        print_result "$candidate"
        return 0
    done

    [ "$CREATE" = "1" ] || die "FreeCAD Mod не найден (проверены: ${CANDIDATE_MODS[*]})"

    # --create: Mod ещё не существует (FreeCAD ставился, но Mod пуст) — используем стандартный путь
    mkdir -p "$XDG_DATA/FreeCAD/Mod"
    print_result "$XDG_DATA/FreeCAD/Mod"
}

main() {
    parse_args "$@"
    find_mod_dir
}

main "$@"
