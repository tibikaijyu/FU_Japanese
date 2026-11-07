function FR_toggleEffects()
	local fr_enabled = status.statusProperty("fr_enabled")

	if fr_enabled then
		text = "^cyan;FRの種族固有効果を無効にしました。^reset;\n\n食性を含め、^yellow;生来の長所も短所もありません^reset;。"
	else
		text = "^cyan;FRの種族固有効果を復元しました。^reset;\n\n生物学的な特性からさまざまな^green;長所^reset;を得る一方、生来の^red;弱点^reset;もあります。"
	end
	status.setStatusProperty("fr_enabled", not fr_enabled)

	resetGUI()
	textTyper.init(cfg.TextData, text)
end