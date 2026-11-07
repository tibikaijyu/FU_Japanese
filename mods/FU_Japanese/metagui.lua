-- metaGUI stub (safe to include)

function init() pane.dismiss()
  _mgcfg = root.assetJson("/panes.config").metaGUI
  if not _mgcfg then -- attempt to use fallback if metaGUI isn't present
    local fb = config.getParameter("fallback")
    if not fb then return player.confirm {
        paneLayout = "/interface/windowconfig/popup.config:paneLayout",
        icon = "/interface/errorpopup/erroricon.png",
        title = "metaGUIエラー",
        message = "metaGUI／StardustLibが見つからず、この操作には代替画面も指定されていません。"
      } end
    if type(fb) ~= "table" or not fb[1] then fb = { "ScriptPane", fb } end
    player.interact(fb[1], fb[2], pane.sourceEntity())
  else
    require(_mgcfg.providerRoot .. "build.lua")
  end
end
