local gears = require("gears")
local os = os;

-- {{{ Wallpaper
-- if beautiful.wallpaper then
--     for s = 1, screen.count() do
--         gears.wallpaper.maximized(beautiful.wallpaper, s, true)
--     end
-- end
-- }}}

-- {{{ Function definitions
--
-- scan directory, and optionally filter outputs
function scandir(directory, filter)
  local homedir = os.getenv("HOME");
  directory = directory:gsub("^~/", homedir .. "/")
  local i, t, popen = 0, {}, io.popen
  if not filter then
    filter = function(s) return true end
  end
  print(filter)
  for filename in popen('find "'..directory..'"'):lines() do
    if filter(filename) then
      i = i + 1
      t[i] = filename
    end
  end
  return t
end

-- }}}

-- configuration - edit to your liking
wp_index = 1
wp_timeout  = 100
wp_path = "~/pictures/"
wp_filter = function(s) return string.match(s,"%.png$") or string.match(s,"%.jpg$") end
wp_files = scandir(wp_path, wp_filter)

wp_index = math.random( 1, #wp_files)
gears.wallpaper.maximized(wp_files[wp_index], s, true)
-- setup the timer
wp_timer = timer { timeout = wp_timeout }
wp_timer:connect_signal("timeout", function()

  -- set wallpaper to current index for all screens
  for s = 1, screen.count() do

    -- get next random index
    wp_index = math.random( 1, #wp_files)

    --  gears.wallpaper.maximized(wp_path .. wp_files[wp_index], s, true)
    gears.wallpaper.maximized(wp_files[wp_index], s, true)
  end

  -- stop the timer (we don't need multiple instances running at the same time)
  wp_timer:stop()


  --restart the timer
  wp_timer.timeout = wp_timeout
  wp_timer:start()
end)

-- initial start when rc.lua is first run
wp_timer:start()

