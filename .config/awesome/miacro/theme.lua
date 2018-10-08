local themepath = "/usr/share/awesome/themes/default/theme.lua";
local xresources = require("beautiful.xresources")
local dpi = xresources.apply_dpi
success, theme = pcall(function() return dofile(themepath) end)

if not success then
  return print("E: error loading theme file " .. theme)
elseif theme then
  theme.font = "Source Code Pro 12"
  theme.menu_height = dpi(23)
  theme.menu_width  = dpi(150)
  return theme
end
