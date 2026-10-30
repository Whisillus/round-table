#!/usr/bin/env bash
set -euo pipefail

module=all
overwrite=false
while (( $# > 0 )); do
    case $1 in
        --module)
            if (( $# < 2 )); then
                printf 'Expected all, skills, or agents after --module.\n' >&2
                exit 2
            fi
            case $2 in
                all|skills|agents) module=$2 ;;
                *)
                    printf 'Invalid module: %s (expected all, skills, or agents).\n' "$2" >&2
                    exit 2
                    ;;
            esac
            shift 2
            ;;
        --overwrite)
            overwrite=true
            shift
            ;;
        --help)
            printf 'Usage: bash install.sh [--module {all|skills|agents}] [--overwrite]\nDefault module: all\n'
            exit 0
            ;;
        *)
            printf 'Unknown argument: %s\nUsage: bash install.sh [--module {all|skills|agents}] [--overwrite]\n' "$1" >&2
            exit 2
            ;;
    esac
done

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
target_dir=${ROUND_TABLE_INSTALL_DIR:-${HOME:?HOME must be set}/.agents}
if [[ $target_dir != /* ]]; then
    printf 'Expected an absolute installation directory: %s\n' "$target_dir" >&2
    exit 2
fi
sources=()
targets=()
if [[ $module == agents || $module == all ]]; then
    sources+=("$repo_dir/agents/GLOBAL-AGENTS.md")
    targets+=("$target_dir/AGENTS.md")
fi
if [[ $module == skills || $module == all ]]; then
    shopt -s nullglob dotglob
    skill_dirs=("$repo_dir"/skills/*)
    if (( ${#skill_dirs[@]} == 0 )); then
        printf 'No skills found in %s/skills\n' "$repo_dir" >&2
        exit 1
    fi
    for skill_dir in "${skill_dirs[@]}"; do
        if [[ ! -d $skill_dir || -L $skill_dir || ! -f $skill_dir/SKILL.md ]]; then
            printf 'Expected a skill directory with SKILL.md: %s\n' "$skill_dir" >&2
            exit 1
        fi
        while IFS= read -r -d '' source; do
            sources+=("$source")
            targets+=("$target_dir/skills/${source#"$repo_dir/skills/"}")
        done < <(find "$skill_dir" -mindepth 1 ! -type d -print0 | sort -z)
    done
fi

# Check the entire selection before copying so known conflicts cause no writes.
failed=false
copy_indices=()
for index in "${!sources[@]}"; do
    source=${sources[index]}
    target=${targets[index]}
    if [[ ! -f $source || ! -r $source || -L $source ]]; then
        printf 'Expected a readable regular source file: %s\n' "$source" >&2
        failed=true
        continue
    fi
    parent=$target
    invalid=false
    while [[ $parent != / ]]; do
        if [[ -L $parent ]]; then
            printf 'Refusing symbolic link in destination: %s\n' "$parent" >&2
            invalid=true
            break
        fi
        if [[ $parent != "$target" && -e $parent && ! -d $parent ]]; then
            printf 'Expected a destination directory: %s\n' "$parent" >&2
            invalid=true
            break
        fi
        parent=$(dirname -- "$parent")
    done
    if [[ $invalid == true ]]; then
        failed=true
        continue
    fi
    if [[ -e $target ]]; then
        if [[ ! -f $target ]]; then
            printf 'Expected a regular destination file: %s\n' "$target" >&2
            failed=true
            continue
        fi
        if cmp -s -- "$source" "$target"; then
            continue
        else
            status=$?
            if (( status != 1 )); then
                printf 'Cannot compare files: %s and %s (exit %s)\n' "$source" "$target" "$status" >&2
                failed=true
                continue
            fi
        fi
        if [[ $overwrite == false ]]; then
            printf 'Conflict: %s (use --overwrite to replace)\n' "$target" >&2
            failed=true
            continue
        fi
    fi
    copy_indices+=("$index")
done
if [[ $failed == true ]]; then
    exit 1
fi

for index in "${copy_indices[@]}"; do
    target=${targets[index]}
    mkdir -p -- "$(dirname -- "$target")"
    cp -- "${sources[index]}" "$target"
    printf 'Installed: %s\n' "$target"
done
printf 'Installation complete: %s file(s) copied.\n' "${#copy_indices[@]}"
