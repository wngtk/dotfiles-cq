# if ! set -q TMUX
#     exec tmux
# end
fish_add_path -gp "$HOME/.neovim/bin"

function pon
    export http_proxy='http://192.168.5.102:7897'
    export https_proxy='http://192.168.5.102:7897'
end
