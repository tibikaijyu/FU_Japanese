
function init()
	widget.setText("textScrollBox.text", "更新情報の初期化中にエラーが発生しました。ログを添付して、次のMODに報告してください：\n"..tostring(status.statusProperty("zb_updatewindow_error", "ztarbound")))
end
