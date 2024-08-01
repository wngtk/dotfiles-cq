local function get_spec_info(filepath)
    -- Initialize version and release variables
    local version = ''
    local release = ''
    local lines = {}

    -- Read lines from the specified file or the current buffer
    if filepath and filepath ~= '' then
        local file = io.open(filepath, 'r')
        if file then
            for line in file:lines() do
                table.insert(lines, line)
            end
            file:close()
        else
            print('File not readable: ' .. filepath)
            return ''
        end
    else
        for _, line in ipairs(vim.api.nvim_buf_get_lines(0, 0, -1, false)) do
            table.insert(lines, line)
        end
    end

    -- Iterate over the lines
    for _, line in ipairs(lines) do
        -- Check if the line contains the version
        if line:match('^Version:') then
            version = line:gsub('^Version:%s*', '')
        -- Check if the line contains the release
        elseif line:match('^Release:') then
            release = line:gsub('^Release:%s*', ''):gsub('%%{%?dist}', '')
        end
    end

    -- Return the version and release
    return version .. '-' .. release
end

local function upstream_spec_path()
    -- Get the current working directory
    local pwd = vim.fn.getcwd()
    -- Get the base name of the current working directory
    local basename = vim.fn.fnamemodify(pwd, ':t')
    -- Construct the file path
    local filepath = pwd .. '/upstream/' .. basename .. '.spec'

    return filepath
end

-- Make the Lua functions available to Vimscript
_G.get_spec_info = get_spec_info
_G.upstream_spec_path = upstream_spec_path

-- Set up the abbreviations
vim.api.nvim_create_autocmd('FileType', {
    pattern = 'spec,gitcommit',
    callback = function()
        vim.cmd('language time en_US.UTF-8')
        vim.cmd('iabbrev <expr> <buffer> dst strftime("%a %b %d %Y") .. " Wang Tiaoke <wangtiaoke@cqsoftware.com.cn> - " .. v:lua.get_spec_info()')
        vim.cmd('iabbrev <expr> <buffer> vst v:lua.get_spec_info(v:lua.upstream_spec_path())')
    end,
})
