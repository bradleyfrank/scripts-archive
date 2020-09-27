  # show cwd always as prefixed path (e.g. ~/D/H/dotfiles)
  local _pwd="" _path="" _num_dirs=0
  readarray -t _path <<< "$(echo "$PWD" | sed "s|^${HOME}|~|" | sed "s|/|\n|g")"
  _num_dirs="${#_path[@]}"
  ((_num_dirs--))

  if [[ "$_num_dirs" -gt 0 ]]; then
    for ((i=0;i<"${_num_dirs}";i++)); do
      _pwd="${_pwd}${_path[$i]:0:1}/"
    done
  fi

  _cwd="${blue}${_pwd}${_path[$_num_dirs]}${reset}"
