local awful = require("awful")
awful.rules = require("awful.rules")
require("awful.autofocus")
-- {{{ Key bindings
globalkeys = awful.util.table.join(
globalkeys,
awful.key({ }, "Print", 
function () 
  awful.util.spawn("scrot -e 'mv $f ~/screenshots/ 2>/dev/null'")
end))
