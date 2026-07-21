_not_enough_secrets() {
    local cur prev words cword
    _init_completion || return

    local commands="version modules encrypt decrypt"

    # find the subcommand, skipping global flags
    local command=""
    local i
    for ((i = 1; i < cword; i++)); do
        case "${words[i]}" in
            -*) ;;
            *)
                command="${words[i]}"
                break
                ;;
        esac
    done

    # complete global flags and command names
    if [[ -z "$command" ]]; then
        if [[ "$cur" == -* ]]; then
            COMPREPLY=($(compgen -W "-h --help -v --verbose --debug" -- "$cur"))
        else
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        fi
        return
    fi

    # complete the value that follows an option
    case "$prev" in
        -m | --module)
            local modules
            modules="$(not-enough-secrets _complete modules 2>/dev/null)"
            COMPREPLY=($(compgen -W "$modules" -- "$cur"))
            return
            ;;
        -o | --output)
            _filedir
            return
            ;;
    esac

    case "$command" in
        modules)
            COMPREPLY=($(compgen -W "-h --help -a --all" -- "$cur"))
            ;;
        encrypt | decrypt)
            if [[ "$cur" == -* ]]; then
                local opts="-h --help -m --module --in-place -o --output -f --force --stdout"
                COMPREPLY=($(compgen -W "$opts" -- "$cur"))
            else
                _filedir
            fi
            ;;
        version)
            COMPREPLY=($(compgen -W "-h --help" -- "$cur"))
            ;;
    esac
}

complete -F _not_enough_secrets not-enough-secrets
